
import csv
import io
import sqlite3
import argparse
import os
import zipfile


DEFAULT_INDEX_PATH = os.path.join(os.path.dirname(__file__), "instance", "food_index.sqlite3")
BATCH_SIZE = 5000
FOOD_TYPES = {
    "foundation_food": "Foundation",
    "sr_legacy_food": "SR Legacy",
    "survey_fndds_food": "Survey (FNDDS)",
    "branded_food": "Branded",
    "experimental_food": "Experimental",
}


def csv_member(archive, name):
    matches = [member for member in archive.namelist()
               if member.rsplit("/", 1)[-1] == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one {name} in the USDA archive; found {len(matches)}.")
    return matches[0]


def csv_records(archive, name):
    with archive.open(csv_member(archive, name)) as binary:
        with io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream:
            yield from csv.DictReader(stream)


def insert_batches(connection, statement, rows):
    batch = []
    count = 0
    for row in rows:
        batch.append(row)
        if len(batch) == BATCH_SIZE:
            connection.executemany(statement, batch)
            count += len(batch)
            batch.clear()
    if batch:
        connection.executemany(statement, batch)
        count += len(batch)
    return count


def build_index(archive_path, index_path=DEFAULT_INDEX_PATH):
    os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)
    temporary_path = f"{index_path}.building"
    if os.path.exists(temporary_path):
        os.remove(temporary_path)
    connection = sqlite3.connect(temporary_path)
    try:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute(
            "CREATE TABLE foods (fdc_id INTEGER PRIMARY KEY, data_type TEXT NOT NULL, "
            "description TEXT NOT NULL, publication_date TEXT, brand_name TEXT, gtin_upc TEXT)"
        )
        with zipfile.ZipFile(archive_path) as archive:
            count = insert_batches(connection,
                "INSERT INTO foods (fdc_id, data_type, description, publication_date) "
                "VALUES (?, ?, ?, ?)",
                ((int(row["fdc_id"]), FOOD_TYPES[row["data_type"]], row["description"],
                  row.get("publication_date"))
                 for row in csv_records(archive, "food.csv")
                 if row["data_type"] in FOOD_TYPES))
            print(f"Imported {count:,} foods", flush=True)
            branded_count = insert_batches(connection,
                "UPDATE foods SET brand_name = ?, gtin_upc = ? WHERE fdc_id = ?",
                ((row.get("brand_name") or row.get("brand_owner") or None,
                  row.get("gtin_upc") or None, int(row["fdc_id"]))
                 for row in csv_records(archive, "branded_food.csv")))
            print(f"Added metadata for {branded_count:,} branded rows", flush=True)
        connection.execute("CREATE INDEX food_barcode_idx ON foods(gtin_upc)")
        connection.execute("CREATE INDEX food_barcode_digits_idx ON foods(ltrim(gtin_upc, '0'))")
        connection.execute(
            "CREATE VIRTUAL TABLE food_search USING fts5(description, brand_name, "
            "content='foods', content_rowid='fdc_id', tokenize='porter unicode61', "
            "prefix='2 3 4')"
        )
        connection.execute("INSERT INTO food_search(food_search) VALUES ('rebuild')")
        connection.commit()
        connection.close()
        os.replace(temporary_path, index_path)
        print(f"Search index ready: {index_path}", flush=True)
        return count
    except Exception:
        connection.close()
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise


def main():
    parser = argparse.ArgumentParser(description="Build the local USDA food search index.")
    parser.add_argument("archive", help="Path to USDA's Full Download CSV ZIP")
    parser.add_argument("--output", default=DEFAULT_INDEX_PATH,
                        help="SQLite index path (defaults to instance/food_index.sqlite3)")
    arguments = parser.parse_args()
    build_index(arguments.archive, arguments.output)


if __name__ == "__main__":
    main()
