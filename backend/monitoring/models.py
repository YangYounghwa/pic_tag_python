from django.db import models

# monitoring/models.py
# IdentityLog 모델 정의
# 이 모델은 사람 인식 로그를 저장하는 데 사용됩니다.
class IdentityLog(models.Model):
    timestamp = models.DateTimeField()
    person_id = models.IntegerField()
    embedding = models.JSONField()  # 임베딩 데이터를 JSON 형태로 저장
    file_path = models.CharField(max_length=255)
    camera_id = models.IntegerField()
    bb_x1 = models.IntegerField()
    bb_y1 = models.IntegerField()
    bb_x2 = models.IntegerField()
    bb_y2 = models.IntegerField()

    class Meta:
        db_table = 'identity_log'  # DB 테이블 이름 명시
        ordering = ['-timestamp']  # 최신순 정렬

    def __str__(self):
        return f"Person {self.person_id} at {self.timestamp}"

