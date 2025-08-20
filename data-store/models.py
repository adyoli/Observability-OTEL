from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        String, nullable=False, index=True
    )
    filename = Column(String, nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    file_path = Column(String, nullable=True)  # Optional: where file is stored
