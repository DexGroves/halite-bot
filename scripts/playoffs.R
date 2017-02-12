library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")


build_call <- function(confname, dim, nopp, seed) {
  call <- paste0(
    "halite -s ",
    seed, " -t -d ",
    "\"", dim, " ", dim, "\" ",
    "\"python3 MyBot.py ", confname, "\" ",
    paste(rep("\"python3 ReferenceBot.py\"", nopp), collapse = " ")
  )
  call
}

run_playoff <- function(nrun, ncore, start_seed,
                        dim, nopp, confname) {
  seeds <- seq(start_seed, start_seed + nrun - 1)
  registerDoMC(ncore)
  results <- foreach(seed = seeds, .combine = c) %dopar% {
    cat(".")
    build_call(confname, dim, nopp, seed) %>%
      system(intern = TRUE) %>%
      paste(collapse = "\n") %>%
      str_extract("(?<=DexBotNeuer, came in rank #)[0-9]")
  }
  system("rm *.hlt")
  table(results)
}
run_playoff(50, 2, 22222, 30, 1, "")
# 28 22
run_playoff(50, 2, 22222, 30, 3, "")
# 23 7 9 11
run_playoff(50, 2, 22222, 30, 3, "")
# 25 8 9 8
# 27 7 9 7
# 29 6 8 7
# 28 8 7 7
# run_playoff(400, 50, 99999, 30, 3, "")

# Master
#   1   2
# 358 142
