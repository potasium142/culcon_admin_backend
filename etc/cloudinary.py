import cloudinary
import cloudinary.uploader
from config import env

uri = f"cloudinary://{env.CLOUDINARY_API_KEY}:{env.CLOUDINARY_API_SECRET}@{env.CLOUDINARY_NAME}"

cloudinary.config(
    api_secret=env.CLOUDINARY_API_SECRET,
    api_key=env.CLOUDINARY_API_KEY,
    cloud_name=env.CLOUDINARY_NAME,
)


def upload(
    image: bytes,
    dir: str,
    public_id: str,
) -> str:
    return cloudinary.uploader.upload(
        image,
        public_id=public_id,
        asset_folder=dir,
    )["url"]
