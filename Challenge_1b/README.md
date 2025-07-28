# Challenge 1b Solution

## Structure

```
Challenge_1b/
├── challenge1b_input.json   # Input config (edit as needed)
├── challenge1b_output.json  # Example output (generated)
├── PDFs/                   # Place your PDF files here
├── Dockerfile              # Build/run containerized solution
├── README.md               # This file
```

## Usage

1. Place your input PDFs in the `PDFs/` folder.
2. Edit `challenge1b_input.json` to reference your PDFs and specify persona/task.
3. Build and run the Docker container:
   ```sh
   docker build -t challenge1b .
   docker run --rm -v $(pwd)/PDFs:/app/input/PDFs -v $(pwd)/output:/app/output challenge1b
   ```
4. Output will be in the `output/` folder as `result.json`.

## Notes

- The container downloads the required model and NLTK data at build time.
- Adjust `requirements.txt` as needed for dependencies.
