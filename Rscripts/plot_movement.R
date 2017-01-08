library("ggplot2")
library("data.table")
library("magrittr")

plot_moves <- function(turn_moves, lims) {
  tmoves <- turn_moves %>%
    {rbind(.[, .(static, origin = TRUE, shape = "1", piece_id, x, y)],
           .[, .(static, origin = FALSE, shape = "10", piece_id, x = tx, y = ty)])}

  ggplot(tmoves[order(piece_id, static)],
         aes(x = x, y = y, group = piece_id)) +
      geom_point(aes(shape = shape, color = origin)) +
      geom_line(data = tmoves[static == FALSE], alpha = 0.33) +
      xlim(lims) +
      scale_y_continuous(trans = "reverse", limits = rev(lims)) +
      ggtitle(turn_moves$turn[1])
}

moves <- fread("moves.txt")
moves[, piece_id := 1:.N, by = turn]
moves[, static := (x == tx & y == ty)]

pdf("moves.pdf")
for (i in seq(max(moves$turn))) {
  gg <- plot_moves(moves[turn == i], lims=c(min(moves$x), max(moves$x)))
  plot(gg)
  cat(".")
}
dev.off()
turn_moves <- moves[turn == i]
plot_moves(turn_moves)
