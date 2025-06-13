import httpx
import time
import json
import logging
import io
from typing import Optional, Any

from enum import Enum
from PIL import Image
from doc_page_extractor import ExtractedResult, TableLayoutParsedFormat
from pdf_craft import DocExtractorProtocol
from tenacity import Retrying, stop_after_attempt, retry_if_exception_type, wait_exponential, retry_if_exception_message
from typing import TypedDict, Literal, Optional
from dataclasses import dataclass
from .convert_cloud_response import convert_data


class QueryTaskResponseData(TypedDict):
  task_id: str
  status: Literal["pending", "in_progress", "completed", "failed", "cancelled"]
  created_at: str
  executed_at: str | None
  completed_at: str | None
  result: Optional[Any]

class QueryTaskResponse(TypedDict):
  success: bool
  data: QueryTaskResponseData

class CloudExtractorErrors(Enum):
  CreateTaskLimit = "Running task limit reached"


class TaskLimitReachedError(Exception):
  def __init__(self):
    super().__init__("Running task limit reached")

@dataclass
class TaskParams:
  image: Image.Image
  extract_formula: bool
  extract_table_format: TableLayoutParsedFormat | None
  ocr_for_each_layouts: bool
  adjust_points: bool


class CloudExtractor(DocExtractorProtocol):

  def __init__(self, base_url: str | None, api_key: str):
    self.base_url = base_url or "https://console.oomol.dev"
    self.api_key = api_key
    self.headers = {
      "Authorization": self.api_key,
    }

  def extract(
    self,
    image: Image.Image,
    extract_formula: bool,
    extract_table_format: TableLayoutParsedFormat | None,
    ocr_for_each_layouts: bool,
    adjust_points: bool,
  ) -> ExtractedResult:
    params = TaskParams(
      image=image,
      extract_formula=extract_formula,
      extract_table_format=extract_table_format,
      ocr_for_each_layouts=ocr_for_each_layouts,
      adjust_points=adjust_points,
    )
    task = self.create_task(params=params)
    assert task is not None, "Task is None"

    task_id = task["data"]["task_id"]
    print(f"task id: {task_id}")
    # Wait for the task to complete
    time.sleep(3)
    task_data = self.get_result_until_success(task_id=task_id)
    assert task_data is not None, "Task data is None"
    return convert_data(task_data)

  def create_task(self, params: TaskParams):
    retrier = Retrying(
      stop=stop_after_attempt(5),
      wait=wait_exponential(multiplier=1, min=10, max=30),
      retry=retry_if_exception_type(TaskLimitReachedError) | retry_if_exception_message("Server disconnected without sending a response."),
      reraise=True,
    )

    try:
      task_resp = retrier(self.send_task_request, params=params)
      return task_resp
    except Exception as e:
      raise e

  def send_task_request(self, params=TaskParams):
    buffer = io.BytesIO()
    params.image.save(buffer, format="PNG")
    buffer.seek(0)
    files = {
      "image": buffer
    }
    data = {
      "extract_formula": params.extract_formula,
      "ocr_for_each_layouts": params.ocr_for_each_layouts,
      "adjust_points": params.adjust_points,
    }
    extract_table_format = params.extract_table_format.value if params.extract_table_format else None
    if extract_table_format is not None:
      data["extract_table_format"] = extract_table_format

    resp = httpx.post(f"{self.base_url}/api/tasks", files=files, data=data, headers=self.headers, timeout=120)
    print(f"send_task_request: {resp.status_code}")
    if self.is_task_limit_reached(resp):
      raise TaskLimitReachedError()
    else:
      if resp.status_code != 200:
        if resp.status_code == 400:
          content = resp.json()
          if content["message"] == "Insufficient quota":
            raise Exception("Insufficient quota")
          else:
            print(content)
            resp.raise_for_status()
        else:
          resp.raise_for_status()
      return resp.json()


  def is_task_limit_reached(self, task: httpx.Response):
    if task.status_code == 400:
      task_data = task.json()
      if task_data["message"] == CloudExtractorErrors.CreateTaskLimit.value:
        return True
    return False

  def query_task(self, task_id: str):
    task_status = httpx.get(f"{self.base_url}/api/tasks?task_id={task_id}", headers=self.headers, timeout=60)


  def get_result_until_success(self, task_id: str, max_retries: int = 30, initial_delay: int = 5) -> Optional[Any]:
    send_request = lambda: httpx.get(
      f"{self.base_url}/api/tasks?task_id={task_id}",
      headers=self.headers,
      timeout=60
    )

    retry_count = 0
    current_delay = initial_delay

    while retry_count < max_retries:
      try:
        task_status = send_request()
        if task_status.status_code != 200:
          print(f"request failed: HTTP {task_status.status_code} - {task_status.text}")
          return None

        task_data: QueryTaskResponse = task_status.json()

        if not task_data["success"]:
          print(f"task get failed: {task_data.get('message')}")
          return None

        result_data = task_data["data"]
        status = result_data["status"]

        if status == "completed":
          print(f"task completed: {task_id}")
          return result_data["result"]

        elif status == "failed":
          print(f"task failed: {task_id} {task_data}")
          return None

        elif status in ["pending", "in_progress"]:
          retry_count += 1
          if retry_count > 1:
            print(f"task ({status}), retry: {retry_count + 1}/{max_retries}")
          time.sleep(current_delay)
          # 指数退避策略，最长等待时间为60秒
          current_delay = min(current_delay * 1.5, 60)
          continue

        else:
          print(f"unknown status: {status}")
          return None

      except Exception as e:
        print(f"request failed: {e}")
        return None

    print(f"task retry max reached: ({max_retries}), task: {task_id}")
    return None
