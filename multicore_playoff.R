library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

build_call <- function(dim, nopp, seed) {
  call <- paste0(
    "halite -s ",
    seed, " -d ",
    "\"", dim, " ", dim, "\" ",
    "\"python3 MyBot.py dexbot.multiway.config\" ",
    paste(rep("\"python3 MyBotBattleMode1.py\"", nopp), collapse = " ")
  )
  call
}


nrun <- 1000
ncore <- 48
start_seed <- 240240
seeds <- seq(start_seed, start_seed + nrun)
system.time({
  registerDoMC(ncore)
  results <- foreach(seed = seeds, .combine = c) %dopar% {
    cat(".")
    build_call(40, 1, seed) %>%
      system(intern = TRUE) %>%
      paste(collapse = "\n") %>%
      str_extract("(?<=DexBot, came in rank #)[0-9]")
  }
  system("rm *.hlt")
})
table(results)

# 1349
# 1399  # Force earlygame moves for bad squares
# 1455  # Trust earlygame further than before
# 1470  # cap at 10
# 1491  # cap at max_val / 2
# 1497  # Earlygame look further out
# 1567  # max wait of 6
# 1579  # max wait of 7

#   1   2   3   4
# 436  54  63 327

#   1   2   3   4
# 580  66  64 222
