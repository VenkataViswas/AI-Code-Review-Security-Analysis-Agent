"""Security issue: missing authorization check."""

def delete_document(request, document_id, database):
    # The handler checks that a user is logged in, but not document ownership.
    if request.user is None:
        raise PermissionError("Login required")
    database.delete_document(document_id)
    return {"deleted": True}
