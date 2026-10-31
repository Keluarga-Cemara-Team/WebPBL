class FirestoreUserRepository:
    def __init__(self, firebase_client):
        self.db = firebase_client.get_db()
        self.col = self.db.collection("users")

    def save(self, user):
        data = {
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "division": user.division
        }
        _, doc_ref = self.col.add(data)
        user.id = doc_ref.id
        return user

    def find_all(self):
        return [doc.to_dict() for doc in self.col.stream()]