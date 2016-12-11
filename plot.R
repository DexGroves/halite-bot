library("plotly")

fread("strto.txt", header = FALSE) %>% as.matrix %>% t %>% {plot_ly(z = ., type = "surface")}
