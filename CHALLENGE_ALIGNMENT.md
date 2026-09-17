# 2026 Challenge Alignment

## Selected challenge

**Build a Junior Astronaut Mission Trainer**

The challenge asks teams to build an interactive game or app that lets students run a lunar or Martian outpost, balance competing engineering demands, and experience how their choices shape mission outcomes.

## Requirement → implementation

| Challenge need | Moon→Mars Mission Trainer response |
|---|---|
| Interactive game or app | `trainer.html` is the public competition front door. |
| Student-focused experience | Plain-language mission cards, limited training credits, immediate debrief, and visible explanations. |
| Lunar or Martian outpost | Two selectable scenarios: Lunar South Pole Outpost and Mars Surface Outpost. |
| Engineering trade-offs | Students cannot select every investment because the scenario has a limited training-credit budget. |
| Competing mission demands | Cards cover dust, darkness, communications, mobility, power, habitation, Mars EDL, food/nutrition, transportation, ascent, and related NASA technology gaps when present in the loaded data. |
| Understand consequences | The debrief shows which architecture nodes have no other loaded technology gaps and which still carry residual dependencies. |
| Educational value | The experience teaches that solving one engineering problem does not imply overall mission readiness. |
| NASA data use | Technology gaps and architecture mappings come from official NASA Moon-to-Mars Revision C XLSX products. |
| Scientific validity | Training mechanics are clearly separated from NASA-derived evidence; no fabricated readiness or survival score is produced. |
| Deeper exploration | Every selected gap can open in the Decision Atlas, 3D Mission Context, and NASA source evidence. |

## Judge story

**Surface:** a student mission game.

**Underneath:** an auditable NASA architecture graph.

That combination is the core differentiator. The trainer is intentionally approachable, while the Decision Atlas, residual-dependency engine, 3D context bridge, and source-level provenance provide technical depth for judges who inspect the implementation.

## Non-goals

The product does not claim to be:

- an operational mission-planning tool;
- an official NASA training system;
- a quantitative probability-of-survival model;
- a flight-readiness certification system;
- a complete physical simulation of a lunar or Martian outpost.

## Submission lock

The competition-facing experience should remain focused on the selected challenge. Earlier unrelated prototype modules may remain in repository history or as technical experiments, but they should not appear in the judge-facing demo flow.
