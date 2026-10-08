import boto3
from PIL import Image
from io import BytesIO
from urllib.parse import unquote_plus
import os

s3 = boto3.client("s3")

MAX_SIZE = (800, 800)
OUTPUT_PREFIX = "resized/"


def lambda_handler(event, context):

    for record in event["Records"]:

        bucket = record["s3"]["bucket"]["name"]

        key = record["s3"]["object"]["key"]
        key = unquote_plus(key)

        # Process only files uploaded to the uploads/ folder
        if not key.startswith("uploads/"):
            continue

        # Download original image
        response = s3.get_object(
            Bucket=bucket,
            Key=key
        )

        image_bytes = response["Body"].read()

        # Open image
        with Image.open(BytesIO(image_bytes)) as image:

            # Resize while keeping the aspect ratio
            image.thumbnail(MAX_SIZE)

            output = BytesIO()

            image_format = image.format or "JPEG"

            # JPEG does not support transparency
            if image_format.upper() == "JPEG":
                image = image.convert("RGB")

            # Save resized image
            image.save(
                output,
                format=image_format,
                optimize=True
            )

            output.seek(0)

        # Create output file name
        file_name = os.path.basename(key)
        output_key = f"{OUTPUT_PREFIX}{file_name}"

        # Upload resized image
        s3.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=output,
            ContentType=response.get(
                "ContentType",
                "image/jpeg"
            )
        )

        print(f"Resized image created: {output_key}")

    return {
        "statusCode": 200,
        "body": "Image resized successfully"
    }