class DataPreprocessor:
    def validate(self, rows):
        """행 단위 데이터 유효성 검사."""
        if not rows:
            return False
        for row in rows:
            if len(row) < 9:
                return False
            if not isinstance(row[0], int) or not isinstance(row[2], int):
                return False
            if not isinstance(row[3], str) or not isinstance(row[4], str):
                return False
            if not isinstance(row[5], int) or not isinstance(row[6], int):
                return False
            if not isinstance(row[7], int) or not isinstance(row[8], int):
                return False
        return True

    def filter_row_outliers(self, rows):
        """행 단위로 바로 판단 가능한 이상치(결측, 타입, bounding box 등)만 제거."""
        filtered = []
        for row in rows:
            # 결측값
            if row[2] is None or not row[1] or not row[4]:
                continue
            # bounding box 좌표가 음수이거나 너무 크면 제외
            if any(coord is not None and (coord < 0 or coord > 10000) for coord in row[6:10]):
                continue
            # 타입 검사
            if not isinstance(row[0], int) or not isinstance(row[2], int):
                continue
            filtered.append(row)
        return filtered