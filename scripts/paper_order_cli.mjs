// Reads an OrderInput as JSON on stdin and prints the Paper order from src/paperOrder.ts.
import { readFileSync } from "node:fs";
import { paperOrder } from "../src/paperOrder.ts";

const input = JSON.parse(readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify(paperOrder(input)));
