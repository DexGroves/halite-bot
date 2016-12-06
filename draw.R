library("plotly")
library("magrittr")
library("data.table")

mat <- fread("mats/vblur10.txt") %>% as.matrix
plot_ly(z = ~mat) %>% add_surface()


mat <- fread("mats/vprod10.txt") %>% as.matrix
plot_ly(z = ~mat) %>% add_surface()

mat <- fread("mats/bstrn10.txt") %>% as.matrix
mat[mat == 99999] = 0
plot_ly(z = ~mat) %>% add_surface()


valu
vprox
mcost
mat <- fread("mats/valu.txt") %>% as.matrix
plot_ly(z = ~mat) %>% add_surface()

mat <- fread("mats/vprox.txt") %>% as.matrix
plot_ly(z = ~mat) %>% add_surface()

mat <- fread("mats/mcost.txt") %>% as.matrix
mat[is.infinite(mat)] <- 0
plot_ly(z = ~mat) %>% add_surface()

