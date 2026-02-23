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

    def find_similar(self, embedding, limit=20):
        cur = self.conn.cursor()
        string_rep = "[" + ",".join(str(x) for x in embedding.tolist()) + "]"

        cur.execute(
            """
            SELECT webviewlink 
            FROM pictures
            ORDER BY embedding <-> %s
            LIMIT %s
            """,
            (string_rep, limit),
        )

        return [row[0] for row in cur.fetchall()]
