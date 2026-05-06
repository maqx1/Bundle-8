import sys
from pipeline import pdf_to_markdown


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python main.py <PDF文件> [输出的md文件]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    md_file = sys.argv[2] if len(sys.argv) > 2 else None

    pdf_to_markdown(pdf_file, md_file)
