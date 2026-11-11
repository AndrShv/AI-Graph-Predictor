import io
from minio import Minio



class MiniO_Service:
    def __init__(self, internal_client: Minio, bucket: str, metrics_service=None):
        self.client = internal_client
        self.bucket = bucket
        self.metrics = metrics_service


    def init_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            raise RuntimeError(f"Storage bucket init failed: {e}") from e

    async def uplaod_file(self, file_bytes: bytes, file_key: str) -> None:
        try:
            stream = io.BytesIO(file_bytes)
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=file_key,
                data=stream,
                length=len(file_bytes),
                content_type="image/png"
            )
            if self.metrics:
                self.metrics.increment_upload_success()
        except Exception as ex:
            if self.metrics:
                self.metrics.increment_upload_failed()
            raise ex

    async def get_file(self, file_key: str) -> bytes:
        response = None
        try:
            response = self.client.get_object(self.bucket, file_key)
            return response.read()
        finally:
            if response:
                response.close()
                response.release_conn()

    async def delete_file(self, file_key: str) -> None:
        try:
            self.client.remove_object(self.bucket, file_key)
            if self.metrics:
                self.metrics.increment_delete_success()
        except Exception as ex:
            if self.metrics:
                self.metrics.increment_delete_failed()
            raise ex

