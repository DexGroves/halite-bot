library("plotly")

fread("gval.txt", header = FALSE) %>% as.matrix %>% {plot_ly(z = ., type = "surface")}
fread("lval.txt", header = FALSE) %>% as.matrix %>% {plot_ly(z = ., type = "surface")}
fread("globval.txt", header = FALSE) %>% as.matrix %>% {plot_ly(z = ., type = "surface")}
fread("strn.txt", header = FALSE) %>% as.matrix %>% {plot_ly(z = ., type = "surface")}

fread("mbval.txt", header = FALSE) %>% as.matrix %>% {plot_ly(z = ., type = "surface")}


fread("mats/mbval1", header = FALSE) %>% as.matrix %>% {plot_ly(z = ., type = "surface")}
