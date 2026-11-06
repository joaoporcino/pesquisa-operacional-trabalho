import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const baseDir = process.cwd();
const dataDir = path.join(baseDir, "dados_modelo");
const previewDir = path.join(baseDir, "previews");
const pythonExe = "C:/Users/070212/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const csvNormalizeCode = "import csv,sys,io; source=io.StringIO(sys.stdin.read()); output=io.StringIO(); csv.writer(output,lineterminator='\\n').writerows(csv.reader(source,delimiter=';')); sys.stdout.write(output.getvalue())";
const workbook = Workbook.create();

function toColumnName(number) {
  let value = number + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

function coerceMatrix(matrix, numericFields, textFields = []) {
  if (matrix.length === 0) return matrix;
  const headers = matrix[0].map((v) => String(v ?? "").replace(/^\uFEFF/, "").trim());
  const numeric = new Set(numericFields);
  const text = new Set(textFields);
  return matrix.map((row, rowIndex) => {
    if (rowIndex === 0) return headers;
    return headers.map((header, colIndex) => {
      const value = row[colIndex] === undefined ? "" : String(row[colIndex]);
      if (value === "") return null;
      if (numeric.has(header) && !text.has(header)) {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : value;
      }
      return value;
    });
  });
}

async function loadCsv(fileName, numericFields = [], textFields = []) {
  const raw = await fs.readFile(path.join(dataDir, fileName), "utf8");
  const converted = spawnSync(pythonExe, ["-c", csvNormalizeCode], {
    input: raw,
    encoding: "utf8",
    windowsHide: true,
  });
  if (converted.status !== 0) {
    throw new Error("Falha ao normalizar CSV: " + fileName + " " + converted.stderr);
  }
  const imported = await Workbook.fromCSV(converted.stdout, { sheetName: "Data" });
  const values = imported.worksheets.getItem("Data").getUsedRange().values;
  return coerceMatrix(values, numericFields, textFields);
}

function columnWidth(header, values) {
  const maxCell = Math.max(
    String(header).length,
    ...values.slice(1).map((row) => String(row[values[0].indexOf(header)] ?? "").length),
  );
  const description = /DESCRICAO|DESCRICOES|OBSERVACAO|NOTA|PREMISSA|TRATAMENTO|REGRA|ENTREGA|ORIGEM|PARETO|MODOS_ESCOLHIDOS|^IDS_|^CODIGOS_/i.test(header);
  const id = /^ID_|^COD|PREDECESSORA|SUCESSORA/i.test(header);
  if (description) return Math.min(Math.max(maxCell + 2, 26), 44);
  if (id) return Math.min(Math.max(maxCell + 2, 12), 22);
  return Math.min(Math.max(maxCell + 2, 10), 20);
}

function setWidths(sheet, matrix, startRow = 1) {
  if (!matrix.length) return;
  const headers = matrix[0];
  const rowCount = matrix.length;
  for (let column = 0; column < headers.length; column++) {
    const header = headers[column];
    const width = columnWidth(header, matrix);
    const range = sheet.getRangeByIndexes(startRow - 1, column, rowCount, 1);
    range.format.columnWidth = width;
  }
}

function formatTable(sheet, matrix, tableName, topRow = 1, topColumn = 1, freezeHeader = false) {
  const rowCount = matrix.length;
  const columnCount = matrix[0].length;
  const left = toColumnName(topColumn - 1);
  const right = toColumnName(topColumn + columnCount - 2);
  const lastRow = topRow + rowCount - 1;
  const address = left + topRow + ":" + right + lastRow;
  const range = sheet.getRange(address);
  range.values = matrix;
  range.format.font = { name: "Arial", size: 10, color: "#202124" };
  range.format.verticalAlignment = "center";
  range.format.wrapText = false;
  const header = sheet.getRange(left + topRow + ":" + right + topRow);
  header.format = {
    fill: "#1F4E78",
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    wrapText: true,
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  header.format.rowHeight = 32;
  const table = sheet.tables.add(address, true, tableName);
  table.showFilterButton = true;
  setWidths(sheet, matrix, topRow);
  let needsAutoFit = false;
  for (let column = 0; column < columnCount; column++) {
    const field = matrix[0][column];
    const letter = toColumnName(topColumn + column - 1);
    const bodyRange = sheet.getRange(letter + (topRow + 1) + ":" + letter + lastRow);
    if (/DESCRICAO|DESCRICOES|OBSERVACAO|NOTA|PREMISSA|TRATAMENTO|REGRA|ENTREGA|ORIGEM|PARETO|MODOS_ESCOLHIDOS|^IDS_|^CODIGOS_/i.test(field)) {
      bodyRange.format.wrapText = true;
      needsAutoFit = true;
    }
    if (field === "CUSTO_MATERIAL_UNITARIO_PONTOS_INDICE") {
      bodyRange.format.numberFormat = "0.00000000";
    } else if (/^PARTICIPACAO_/i.test(field)) {
      bodyRange.format.numberFormat = "0.0%";
    } else if (/CUSTO|PONTOS|DIFERENCA|INDICE|INDIRETO|TAXA/i.test(field)) {
      bodyRange.format.numberFormat = "#,##0.0000";
    } else if (/QUANTIDADE|DURACAO|_DIAS|PRODUTIVIDADE|MULTIPLICADOR|HORAS_/i.test(field)) {
      bodyRange.format.numberFormat = "#,##0.00";
    } else if (/PESSOAS|DISPONIBILIDADE/i.test(field)) {
      bodyRange.format.numberFormat = "#,##0";
    }
  }
  if (needsAutoFit && lastRow > topRow + 1) {
    sheet.getRange(left + (topRow + 1) + ":" + right + lastRow).format.autofitRows();
  }
  if (freezeHeader && topRow === 1) sheet.freezePanes.freezeRows(1);
  return { range, matrix, address };
}

function addSectionTitle(sheet, row, title) {
  const cell = sheet.getRange("A" + row);
  cell.values = [[title]];
  cell.format = { font: { name: "Arial", size: 11, bold: true, color: "#1F1F1F" } };
  cell.format.rowHeight = 22;
}

async function addCsvSheet(name, fileName, numericFields, tableName, textFields = []) {
  const matrix = await loadCsv(fileName, numericFields, textFields);
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  formatTable(sheet, matrix, tableName, 1, 1, true);
  return { sheet, matrix };
}

const comparisons = await loadCsv(
  "comparacao_cenarios.csv",
  [
    "PRAZO_DIAS_UTEIS",
    "CUSTO_FIXO_INDICE",
    "CUSTO_DIRETO_INDICE",
    "CUSTO_INDIRETO_PRAZO_INDICE",
    "CUSTO_INDIRETO_EFETIVO_INDICE",
    "CUSTO_TOTAL_INDICE",
  ],
);
const checks = JSON.parse(await fs.readFile(path.join(dataDir, "verificacoes.json"), "utf8"));
const baseSummary = JSON.parse(await fs.readFile(path.join(dataDir, "resumo_cenario_base.json"), "utf8"));
const optimizedSummary = JSON.parse(await fs.readFile(path.join(dataDir, "resumo_cenario_otimizado.json"), "utf8"));

const summary = workbook.worksheets.add("Resumo");
summary.showGridLines = false;
summary.getRange("A1").values = [["Base acadêmica para otimização tempo-custo"]];
summary.getRange("A1").format = { font: { name: "Arial", size: 15, bold: true, color: "#1F1F1F" } };
summary.getRange("A1").format.rowHeight = 28;
summary.getRange("A2").values = [["12 atividades sintéticas · 1 pool compartilhado por família · não representa prazo integral do S11D · custos sem moeda"]];
summary.getRange("A2").format = { font: { name: "Arial", size: 10, italic: true, color: "#555555" } };

const compareRows = comparisons.slice(1);
const comparisonTable = [
  ["Cenário", "Prazo (dias úteis)", "Custo fixo", "Custo direto", "Indireto por prazo", "Indireto por efetivo", "Custo total"],
  ...compareRows.map((row) => [
    row[0],
    Number(row[1]),
    Number(row[2]),
    Number(row[3]),
    Number(row[4]),
    Number(row[5]),
    Number(row[6]),
  ]),
];
formatTable(summary, comparisonTable, "ScenarioComparison", 4, 1, false);
summary.getRange("B5:G7").format.numberFormat = "#,##0.00";
summary.getRange("A5:A7").format.wrapText = true;
summary.getRange("A5:A7").format.rowHeight = 32;

addSectionTitle(summary, 10, "Verificações do recorte");
const checkRows = [
  ["Verificação", "Resultado"],
  ["Atividades executáveis", checks.atividades_execucao],
  ["Relações FS", checks.precedencias_fs],
  ["Modos de formação de equipe", checks.equipes_perfil],
  ["Habilitações atividade-modo", checks.habilitacoes],
  ["Pools compartilhados", checks.pools_recursos_compartilhados],
  ["Rede sem ciclos", checks.rede_acyclic ? "APROVADO" : "FALHOU"],
  ["Custo padrão conciliado à EAP", checks.direto_padrao_reconciliado_com_eap ? "APROVADO" : "FALHOU"],
  ["Capacidade dos pools no cenário otimizado", checks.restricoes_capacidade_cenario_otimizado],
  ["Solução MILP ótima", optimizedSummary.otimo_comprovado ? "SIM" : "NÃO"],
  ["Gap MIP", Number(optimizedSummary.gap_mip)],
  ["Prazo CPM sem recursos (dias úteis)", Number(checks.cpm_sem_recursos_dias)],
  ["Prazo base com recursos (dias úteis)", Number(checks.cen_base_com_recursos_dias)],
  ["Prazo MILP otimizado (dias úteis)", Number(optimizedSummary.prazo_dias_uteis)],
];
formatTable(summary, checkRows, "ModelChecks", 11, 1, false);
summary.getRange("A1:G24").format.font = { name: "Arial", size: 10, color: "#202124" };
summary.getRange("A1").format.font = { name: "Arial", size: 15, bold: true, color: "#1F1F1F" };
summary.getRange("A2").format.font = { name: "Arial", size: 10, italic: true, color: "#555555" };
summary.getRange("A4:G4").format.font = { name: "Arial", size: 10, bold: true, color: "#FFFFFF" };
summary.getRange("A11:B11").format.font = { name: "Arial", size: 10, bold: true, color: "#FFFFFF" };
summary.getRange("A1:A1").format.columnWidth = 34;
summary.getRange("B1:B24").format.columnWidth = 20;
summary.getRange("C1:G7").format.columnWidth = 19;
summary.getRange("G1:G24").format.columnWidth = 19;

await addCsvSheet(
  "Premissas",
  "premissas.csv",
  ["VALOR"],
  "AssumptionsTable",
);
const assumptionsSheet = workbook.worksheets.getItem("Premissas");
assumptionsSheet.getRange("A1:A20").format.columnWidth = 32;
assumptionsSheet.getRange("B1:B20").format.columnWidth = 46;
assumptionsSheet.getRange("C1:C20").format.columnWidth = 34;
assumptionsSheet.getRange("D1:D20").format.columnWidth = 22;
assumptionsSheet.getRange("E1:E20").format.columnWidth = 72;
await addCsvSheet(
  "Atividades",
  "atividades.csv",
  [
    "QUANTIDADE",
    "PONTOS_CUSTO_EAP_ORIGEM",
    "PARTICIPACAO_MATERIAL_PREMISSA",
    "PRODUTIVIDADE_PADRAO_UNID_DIA",
    "DURACAO_PADRAO_DIAS",
    "O_PADRAO_DIAS",
    "M_PADRAO_DIAS",
    "P_PADRAO_DIAS",
    "TE_PERT_PADRAO_DIAS",
  ],
  "ActivitiesTable",
);
await addCsvSheet(
  "Precedencias",
  "precedencias.csv",
  ["LAG_DIAS"],
  "PrecedenceTable",
);
await addCsvSheet(
  "Equipes",
  "equipes.csv",
  [
    "MULTIPLICADOR_PRODUTIVIDADE",
    "MULTIPLICADOR_CUSTO_DIARIO",
    "PESSOAS_POR_EQUIPE",
    "HORAS_POR_DIA",
  ],
  "TeamsTable",
);
await addCsvSheet(
  "Recursos",
  "recursos_compartilhados.csv",
  ["DISPONIBILIDADE"],
  "SharedResourcesTable",
);
const resourceSheet = workbook.worksheets.getItem("Recursos");
resourceSheet.getRange("A1:A20").format.columnWidth = 22;
resourceSheet.getRange("B1:B20").format.columnWidth = 12;
resourceSheet.getRange("C1:C20").format.columnWidth = 34;
resourceSheet.getRange("D1:D20").format.columnWidth = 17;
resourceSheet.getRange("E1:E20").format.columnWidth = 27;
resourceSheet.getRange("F1:F20").format.columnWidth = 52;
resourceSheet.getRange("G1:G20").format.columnWidth = 54;
resourceSheet.getRange("A1:G1").format.rowHeight = 48;
await addCsvSheet(
  "Alternativas",
  "habilitacoes_alternativas.csv",
  [
    "QUANTIDADE",
    "PRODUTIVIDADE_UNID_DIA",
    "DURACAO_DIAS",
    "O_DIAS",
    "M_DIAS",
    "P_DIAS",
    "TE_PERT_DIAS",
    "PESSOAS_EQUIPE",
    "CUSTO_EQUIPE_DIA_PONTOS_INDICE",
    "CUSTO_EQUIPE_HORA_PONTOS_INDICE",
    "CUSTO_MATERIAL_UNITARIO_PONTOS_INDICE",
    "CUSTO_MATERIAL_TOTAL_PONTOS_INDICE",
    "CUSTO_DIRETO_TOTAL_INDICE",
    "CUSTO_DIRETO_FONTE_EAP_INDICE",
    "DIF_DIRETO_VS_EAP_INDICE",
    "CUSTO_INDIRETO_EFETIVO_INDICE",
  ],
  "AlternativesTable",
);
await addCsvSheet(
  "Sensibilidade",
  "sensibilidade_indiretos.csv",
  [
    "TAXA_PRAZO",
    "TAXA_PESSOA_DIA",
    "PRAZO_DIAS",
    "CUSTO_DIRETO",
    "PESSOA_DIAS",
    "INDIRETO_PRAZO",
    "INDIRETO_PESSOA_DIA",
    "CUSTO_TOTAL_CASO",
    "CUSTO_TOTAL_TAXAS_BASE",
    "GAP_MIP",
  ],
  "IndirectCostSensitivity",
);
const sensitivitySheet = workbook.worksheets.getItem("Sensibilidade");
for (const [column, width] of Object.entries({
  A: 13, B: 19, C: 15, D: 18, E: 14, F: 16, G: 14, H: 18, I: 23,
  J: 21, K: 26, L: 46, M: 15, N: 12, O: 12, P: 16, Q: 44,
})) {
  sensitivitySheet.getRange(column + "1:" + column + "20").format.columnWidth = width;
}
sensitivitySheet.getRange("A1:Q1").format.rowHeight = 46;
await addCsvSheet(
  "Fronteira",
  "fronteira_prazo_custo_amostral.csv",
  [
    "PRAZO_DIAS",
    "CUSTO_DIRETO",
    "PESSOA_DIAS",
    "CUSTO_TOTAL_BASE",
  ],
  "SampleCostTimeFrontier",
);
const frontierSheet = workbook.worksheets.getItem("Fronteira");
for (const [column, width] of Object.entries({
  A: 18, B: 14, C: 16, D: 14, E: 20, F: 34, G: 30, H: 48,
})) {
  frontierSheet.getRange(column + "1:" + column + "20").format.columnWidth = width;
}
frontierSheet.getRange("A1:H1").format.rowHeight = 44;

const scheduleSheet = workbook.worksheets.add("Cronogramas");
scheduleSheet.showGridLines = false;
let row = 1;
const scheduleSpecs = [
  {
    title: "PERT/CPM lógico, sem capacidade de recursos",
    file: "PERT_CPM_sem_recursos.csv",
    table: "CpmReference",
    nums: [
      "DURACAO_DIAS", "O_DIAS", "M_DIAS", "P_DIAS", "TE_PERT_DIAS", "ES_DIAS", "EF_DIAS",
      "LS_DIAS", "LF_DIAS", "FOLGA_DIAS",
    ],
  },
  {
    title: "Referência serial factível, modos padrão e pools compartilhados",
    file: "cenario_base_com_equipes.csv",
    table: "ResourceBase",
    nums: [
      "INICIO_DIA", "FIM_DIA", "DURACAO_DIAS", "QUANTIDADE", "PRODUTIVIDADE_UNID_DIA",
      "PESSOAS_EQUIPE", "CUSTO_DIRETO_INDICE", "CUSTO_INDIRETO_EFETIVO_INDICE",
    ],
  },
  {
    title: "MRCPSP/MILP: escolha de modo e início em conjunto",
    file: "cenario_otimizado.csv",
    table: "OptimizedSchedule",
    nums: [
      "INICIO_DIA", "FIM_DIA", "DURACAO_DIAS", "QUANTIDADE", "PRODUTIVIDADE_UNID_DIA",
      "PESSOAS_EQUIPE", "CUSTO_EQUIPE_DIA_PONTOS_INDICE",
      "CUSTO_MATERIAL_TOTAL_PONTOS_INDICE", "CUSTO_DIRETO_INDICE",
      "CUSTO_INDIRETO_EFETIVO_INDICE",
    ],
  },
];
for (let index = 0; index < scheduleSpecs.length; index++) {
  const spec = scheduleSpecs[index];
  addSectionTitle(scheduleSheet, row, spec.title);
  const matrix = await loadCsv(spec.file, spec.nums);
  formatTable(scheduleSheet, matrix, spec.table, row + 1, 1, false);
  row += matrix.length + 3;
}

const costSheet = workbook.worksheets.add("Custos");
costSheet.showGridLines = false;
addSectionTitle(costSheet, 1, "Mobilização fixa (incluída uma vez)");
const fixedCosts = await loadCsv(
  "custos_fixos.csv",
  ["CUSTO_FIXO_PONTOS_INDICE"],
);
formatTable(costSheet, fixedCosts, "FixedCosts", 2, 1, false);
const costReconciliation = await loadCsv(
  "conciliacao_custos.csv",
  ["CUSTO_PONTOS_EAP_ORIGEM", "CUSTO_DIRETO_EQUIPE_PADRAO", "DIFERENCA"],
);
addSectionTitle(costSheet, fixedCosts.length + 5, "Conciliação: custo direto padrão versus pontos EAP");
formatTable(
  costSheet,
  costReconciliation,
  "CostReconciliation",
  fixedCosts.length + 6,
  1,
  false,
);

const decimalHeaders = new Set([
  "QUANTIDADE", "PONTOS_CUSTO_EAP_ORIGEM", "PARTICIPACAO_MATERIAL_PREMISSA",
  "PRODUTIVIDADE_PADRAO_UNID_DIA", "DURACAO_PADRAO_DIAS", "O_PADRAO_DIAS", "M_PADRAO_DIAS",
  "P_PADRAO_DIAS", "TE_PERT_PADRAO_DIAS", "LAG_DIAS", "MULTIPLICADOR_PRODUTIVIDADE",
  "MULTIPLICADOR_CUSTO_DIARIO", "PESSOAS_POR_EQUIPE", "DISPONIBILIDADE", "HORAS_POR_DIA",
  "PRODUTIVIDADE_UNID_DIA", "DURACAO_DIAS", "O_DIAS", "M_DIAS", "P_DIAS", "TE_PERT_DIAS",
  "PESSOAS_EQUIPE", "CUSTO_EQUIPE_DIA_PONTOS_INDICE", "CUSTO_EQUIPE_HORA_PONTOS_INDICE",
  "CUSTO_MATERIAL_UNITARIO_PONTOS_INDICE", "CUSTO_MATERIAL_TOTAL_PONTOS_INDICE",
  "CUSTO_DIRETO_TOTAL_INDICE", "CUSTO_DIRETO_FONTE_EAP_INDICE", "DIF_DIRETO_VS_EAP_INDICE",
  "CUSTO_INDIRETO_EFETIVO_INDICE", "INICIO_DIA", "FIM_DIA", "ES_DIAS", "EF_DIAS", "LS_DIAS",
  "LF_DIAS", "FOLGA_DIAS", "CUSTO_DIRETO_INDICE", "CUSTO_FIXO_PONTOS_INDICE",
  "CUSTO_PONTOS_EAP_ORIGEM", "CUSTO_DIRETO_EQUIPE_PADRAO", "DIFERENCA",
  "PRAZO_DIAS_UTEIS", "CUSTO_FIXO_INDICE", "CUSTO_DIRETO_INDICE",
  "CUSTO_INDIRETO_PRAZO_INDICE", "CUSTO_INDIRETO_EFETIVO_INDICE", "CUSTO_TOTAL_INDICE",
]);

workbook.recalculate();

const summaryCheck = await workbook.inspect({
  kind: "table",
  range: "Resumo!A1:G24",
  include: "values,formulas",
  tableMaxRows: 24,
  tableMaxCols: 8,
});
const errorCheck = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
if (/\"error\"/.test(errorCheck.ndjson)) {
  throw new Error("Foi encontrado um erro de fórmula: " + errorCheck.ndjson);
}

await fs.mkdir(previewDir, { recursive: true });
for (const sheetName of ["Resumo", "Premissas", "Atividades", "Precedencias", "Equipes", "Recursos", "Alternativas", "Cronogramas", "Sensibilidade", "Fronteira", "Custos"]) {
  const rendered = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, sheetName + ".png"), new Uint8Array(await rendered.arrayBuffer()));
}

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(baseDir, "Base_Otimizacao_Piloto.xlsx");
await xlsx.save(outputPath);
console.log(JSON.stringify({
  output: outputPath,
  summary: summaryCheck.ndjson,
  formulaErrors: errorCheck.ndjson,
  previewSheets: ["Resumo", "Premissas", "Atividades", "Precedencias", "Equipes", "Recursos", "Alternativas", "Cronogramas", "Sensibilidade", "Fronteira", "Custos"],
  sourceSummary: baseSummary,
  optimizedSummary: optimizedSummary,
}, null, 2));
