<div align=center>
  <h1>PDF Craft</h1>
  <p>
    <a href="https://github.com/oomol-flows/pdf-craft/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/oomol-flows/pdf-craft" alt="license" /></a>
  </p>
  <p><a href="https://hub.oomol.com/package/pdf-craft?open=true" target="_blank"><img src="https://static.oomol.com/assets/button.svg" alt="在 OOMOL Studio 中打开" /></a></p>
</div>

[![关于 PDF craft](./docs/images/youtube.png)](https://www.youtube.com/watch?v=EpaLC71gPpM)

一个为使用 [pdf-craft](https://github.com/oomol-lab/pdf-craft) 项目提供可视化模块的 [OOMOL](https://hub.oomol.com/) 包。


## 介绍

PDF Craft 可以将 PDF 文件转换为各种其他格式。该项目专注于处理扫描书籍的 PDF 文件。如果您遇到任何问题或有任何建议，请提交 [issues](https://github.com/oomol-lab/pdf-craft/issues)。

该项目可以逐页读取 PDF，使用 [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO) 结合我编写的算法从书页中提取文本，并过滤掉页眉、页脚、脚注和页码等元素。在跨页过程中，算法会妥善处理前后页之间的连接问题，最终生成语义连贯的文本。书页将使用 [OnnxOCR](https://github.com/jingsongliujing/OnnxOCR) 进行文字识别。并使用 [layoutreader](https://github.com/ppaanngggg/layoutreader) 确定符合人类习惯的阅读顺序。

仅使用这些可以本地执行的 AI 模型（使用本地图形设备加速），就可以将 PDF 文件转换为 Markdown 格式。这适用于论文或小册子。

但是，如果您想要解析书籍（通常超过 100 页），建议将其转换为 [EPUB](https://zh.wikipedia.org/wiki/EPUB) 格式文件。在转换过程中，该库会将本地 OCR 识别的数据传递给 [大语言模型（LLM）](https://zh.wikipedia.org/wiki/大型语言模型)，通过特定信息（如目录等）构建书籍结构，最终生成带有目录和章节的 EPUB 文件。在解析和构建过程中，每页的注释和引用信息将通过 LLM 读取，然后以新的格式在 EPUB 文件中呈现。此外，LLM 可以在一定程度上纠正 OCR 错误。这一步骤无法完全在本地执行。您需要配置 LLM 服务。建议使用 [DeepSeek](https://www.deepseek.com/)。该库的提示基于 V3 模型调试。
