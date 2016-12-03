# v <- fread("value.txt", sep = "\t")

# v[, pixel_id := paste(V1, V2)]
# v[, iterind := 1:.N, by = pixel_id]
# v[, t := 1:.N]

# library("ggplot2")
# ggplot(v[1:50], aes(x = t, y = V4, group = pixel_id, color = pixel_id)) + geom_line()

scanchanges <- function(vec) {
  out <- c()
  last <- -1
  for (v in vec) {
    if (v == last) {
      out <- c(out, 0)
    } else {
      out <- c(out, 1)
      last <- v
    }
  }
  out
}

v <- fread("value.txt")


v[, x := (x + mean(x)) %% 50]
v[, y := (y + mean(y)) %% 50]
v[, val := scale(val), by = turn]
v[, nborder := .N, by = turn]
v[, capd := scanchanges(nborder)]
v[, cumcapd := cumsum(capd)]
v[, capd := max(capd), by = turn]
v[, cumcapd := max(cumcapd), by = turn]



library("ggplot2")
library("ggrepel")

gg <- ggplot(v[turn == 1], aes(x = x, y = -1 * y, color = val,
                               label = round(val, 3))) +
        geom_point() +
        geom_label_repel()
plot(gg)



pdf("valstime.pdf")
for (t in seq(max(v$cumcapd))) {
  gg <- ggplot(v[capd == 1 & cumcapd == t], aes(x = x, y = -1 * y, color = val,
                                 label = round(val, 3))) +
          geom_point() +
          geom_label_repel()
  plot(gg)
  cat(".")
}
dev.off()
