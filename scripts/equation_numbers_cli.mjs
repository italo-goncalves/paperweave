// Reads {nodes: {id: {tiers}}, order: [ids]} as JSON on stdin and prints {label: number}
// from src/equations.ts, the app's equation numbering.
import { readFileSync } from "node:fs";
import { numberEquations } from "../src/equations.ts";

const { nodes, order } = JSON.parse(readFileSync(0, "utf8"));
const eqs = numberEquations(nodes, order);
process.stdout.write(JSON.stringify(Object.fromEntries(Object.values(eqs).map((e) => [e.label, e.number]))));
