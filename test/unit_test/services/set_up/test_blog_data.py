from dtos.request.blog import BlogCreation

def get_sample_blog_dto_1():
    return BlogCreation(
        title="Test Blog",
        description="This is a description.",
        markdown_text="## Markdown content here.",
        infos={"tags": "ai,test"}
    )

