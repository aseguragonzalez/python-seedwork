document$.subscribe(({ body }) => {
  mermaid.initialize({ startOnLoad: false })
  mermaid.run({ nodes: body.querySelectorAll(".mermaid") })
})
