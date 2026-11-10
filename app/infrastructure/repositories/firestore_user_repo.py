from typing import List, Optional, Any
from app.core.entities.user import User
from app.core.interfaces.repositories import IUserRepository

class FirestoreUserRepository(IUserRepository):
    def __init__(self, firebase_client):
        self.db = firebase_client.get_db()
        self.col = self.db.collection("users")

    def _doc_to_entity(self, doc_id: str, data: dict) -> User:
        return User(
            id=doc_id,
            username=data.get("username", doc_id),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            full_name=data.get("full_name", ""),
            role=data.get("role", "admin"),
            division=data.get("division", "Pusat Riset PBL"),
            created_at=data.get("created_at")
        )

    def save(self, user: User) -> User:
        data = {
            "username": user.username,
            "email": user.email,
            "password_hash": user.password_hash,
            "full_name": user.full_name,
            "role": user.role,
            "division": user.division,
            "created_at": user.created_at
        }
        if user.id:
            self.col.document(str(user.id)).set(data, merge=True)
        else:
            _, doc_ref = self.col.add(data)
            user.id = doc_ref.id
        return user

    def find_by_id(self, user_id: Any) -> Optional[User]:
        doc = self.col.document(str(user_id)).get()
        if not doc.exists:
            return None
        return self._doc_to_entity(doc.id, doc.to_dict())

    def find_by_identifier(self, identifier: str) -> Optional[User]:
        clean_id = identifier.strip().lower()
        # Query by username
        docs = list(self.col.where("username", "==", clean_id).limit(1).stream())
        if not docs:
            # Fallback query by email
            docs = list(self.col.where("email", "==", clean_id).limit(1).stream())
        if docs:
            d = docs[0]
            return self._doc_to_entity(d.id, d.to_dict())
        return None

    def find_all(self) -> List[User]:
        results = []
        for doc in self.col.stream():
            results.append(self._doc_to_entity(doc.id, doc.to_dict()))
        return results

    def count(self) -> int:
        return len(list(self.col.stream()))
