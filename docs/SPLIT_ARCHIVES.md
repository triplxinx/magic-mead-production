# Split ZIP upload and restoration

The script [tools/split_archive.py](../tools/split_archive.py) splits an existing ZIP into byte-for-byte 20 MiB chunks. This is **not** a multi-volume ZIP: each part is a binary fragment and must be restored before extraction.

```bash
python tools/split_archive.py split /path/to/Magic-Mead-Spread-Originals.zip --out ./upload-parts
# Commit upload-parts/*.part* and upload-parts/*.manifest.json, subject to public release approval.
python tools/split_archive.py restore ./upload-parts/Magic-Mead-Spread-Originals.zip.manifest.json --out ./restored --extract
```

Every chunk and reconstructed ZIP is SHA-256 verified. Existing destinations are not overwritten. Extraction checks for path traversal and limits total uncompressed size to 2 GiB. Inspect archive contents for restricted/private files and ensure no symlinks or unusual entries before publication.

**GitHub does not unpack files on upload.** GitHub Actions can run the restore command for testing or artifact creation, but extracted outputs are ephemeral until deliberately published. Publishing every extracted binary back into Git may make the repository very large; prefer approved release assets or Git LFS for large art sets.

**Status:** helper uploaded; original Library archives and images have not yet been uploaded, split or extracted.
