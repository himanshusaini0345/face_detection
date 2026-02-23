from imgbeddings import imgbeddings


class EmbeddingGenerator:
    def __init__(self):
        self.ibed = imgbeddings()

    def generate(self, image):
        embedding = self.ibed.to_embeddings(image)
        return embedding[0]
