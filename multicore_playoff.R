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
    "\"python3 MyBotBattleMode1.py\" ",
    paste(rep("\"python3 MyBot.py\"", nopp), collapse = " ")
  )
  call
}


nrun <- 2000
ncore <- 48
start_seed <- 240240
seeds <- seq(start_seed, start_seed + nrun)
system.time({
  registerDoMC(ncore)
  results <- foreach(seed = seeds, .combine = c) %dopar% {
    cat(".")
    build_call(20, 1, seed) %>%
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
