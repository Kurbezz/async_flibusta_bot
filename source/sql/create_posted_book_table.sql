CREATE TABLE IF NOT EXISTS posted_book 
(
    book_id INTEGER NOT NULL,
    file_type VARCHAR(4) NOT NULL,
    file_id VARCHAR(128) NOT NULL,
    PRIMARY KEY (book_id, file_type)
);
ALTER TABLE posted_book OWNER TO {};