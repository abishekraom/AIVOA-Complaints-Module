from sqlalchemy import text

def test_embedding_index_uses_hnsw(_test_database):
    with _test_database.connect() as conn:
        indexdef = conn.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname = 'complaints_embedding_idx'")
        ).scalar_one()

    assert "USING hnsw" in indexdef
