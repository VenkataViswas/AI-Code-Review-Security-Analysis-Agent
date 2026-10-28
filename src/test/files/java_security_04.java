// Security issue: missing object-level authorization check.
class DocumentService {
    public void deleteDocument(User user, String documentId, DocumentRepository repository) {
        if (user == null) {
            throw new SecurityException("Login required");
        }
        // Missing check that the user owns or may delete this document.
        repository.deleteById(documentId);
    }
}

class User {}
interface DocumentRepository {
    void deleteById(String documentId);
}
