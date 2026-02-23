# repository/photo_repository.py

from collections import defaultdict


GAP_RATIO = 1.0 # best/second ratio — must be below this to count as a match


class PhotoRepository:
    def __init__(self, conn):
        self.conn = conn

    def save_embedding(self, file_id, webviewlink, embedding):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO pictures (file_id, webviewlink, embedding)
            VALUES (%s, %s, %s)
            """,
            (file_id, webviewlink, embedding.tolist()),
        )
        self.conn.commit()

    def find_similar(self, embedding, limit=50) -> list[str]:
        """
        1. Fetch top `limit` closest face embeddings from DB
        2. Apply gap-ratio check — best distance must be < GAP_RATIO * second best
           to confirm it's a real match and not just the closest of bad options
        3. Group passing results by webviewlink (vote counting)
        4. Return webviewlinks sorted by votes desc, then best distance asc
        """
        cur = self.conn.cursor()
        string_rep = "[" + ",".join(str(x) for x in embedding.tolist()) + "]"

        cur.execute(
            """
            SELECT webviewlink, embedding <-> %s AS distance
            FROM pictures
            ORDER BY distance
            LIMIT %s
            """,
            (string_rep, limit),
        )
        rows = cur.fetchall()

        if not rows:
            return []

        # gap-ratio check using top 2
        best_dist = rows[0][1]
        second_dist = rows[1][1] if len(rows) > 1 else float("inf")
        ratio = best_dist / second_dist

        if ratio >= GAP_RATIO:
            # best match is not clearly closer than second best — no confident match
            return []

        # accumulate votes for all rows that pass the absolute cutoff
        # cutoff = best_dist * (1 / GAP_RATIO) gives a natural upper bound
        cutoff = best_dist / GAP_RATIO

        votes = defaultdict(int)
        best_link = defaultdict(lambda: float("inf"))

        for webviewlink, distance in rows:
            if distance > cutoff:
                break  # rows are ordered — no point continuing
            votes[webviewlink] += 1
            best_link[webviewlink] = min(best_link[webviewlink], distance)

        return sorted(votes.keys(), key=lambda link: (-votes[link], best_link[link]))
