#let q1 = json("../results/q1.json")
#let q2 = json("../results/q2.json")
#let q3 = json("../results/q3.json")
#let q4 = json("../results/q4.json")
#let sensitivity = json("../results/sensitivity.json")
#let validation = json("../results/validation.json")
#let simulations = json("../results/simulations.json")
#let parameters = json("../inputs/parameters.json")
#let f(x, digits: 2) = {
  let s = str(calc.round(x, digits: digits))
  let parts = s.split(".")
  if digits == 0 { parts.at(0) } else {
    let tail = if parts.len() > 1 { parts.at(1) } else { "" }
    parts.at(0) + "." + tail + "0" * calc.max(0, digits - tail.len())
  }
}
#let bitstr(bits) = bits.map(str).join("")
#let r4(target, n) = q4.find(r => r.target == target and r.N_per_node == n)
#let best-sim(target) = simulations.find(r => r.question == target and r.at("label", default: "") == "best")
#let data-table(header, rows, caption, columns: auto) = {
  let cols = if columns == auto { header.len() } else { columns }
  figure(
    table(
      columns: cols, align: center, stroke: none, inset: (x: 0.55em, y: 0.5em),
      table.hline(y: 0, stroke: 0.8pt),
      table.header(..header.map(strong)),
      table.hline(y: 1, stroke: 0.5pt),
      ..rows.flatten(),
      table.hline(stroke: 0.8pt),
    ),
    caption: caption, kind: table,
  )
}
