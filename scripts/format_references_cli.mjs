// Reads references.yaml fields as JSON on stdin and prints {key: {label, text}} from src/references.ts.
import { readFileSync } from "node:fs";
import { formatReferences } from "../src/references.ts";

process.stdout.write(JSON.stringify(formatReferences(JSON.parse(readFileSync(0, "utf8")))));
