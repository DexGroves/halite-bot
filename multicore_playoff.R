library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

build_call <- function(confname, dim, nopp, seed) {
  call <- paste0(
    "halite -t -s ",
    seed, " -d ",
    "\"", dim, " ", dim, "\" ",
    "\"python3 MyBot.py ", confname, "\" ",
    paste(rep("\"python3 MyBotBattleMode1.py\"", nopp), collapse = " ")
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
      str_extract("(?<=DexBot, came in rank #)[0-9]")
  }
  system("rm *.hlt")
  table(results)
}


nrun <- 500
ncore <- 45
start_seed <- 40240

for (nopp in seq(2, 3, 1)) {
  for (dim in c(20, 50)) {
    dc <- run_playoff(nrun,  ncore, start_seed, dim, nopp, "dexbot.config")
    dmc <- run_playoff(nrun, ncore, start_seed, dim, nopp, "dexbot.multiway.config")
    dhc <- run_playoff(nrun, ncore, start_seed, dim, nopp, "dexbot.headsup.config")
    d3c <- run_playoff(nrun, ncore, start_seed, dim, nopp, "dexbot.threeway.config")
    obj <- list(dim = dim, nopp = nopp, dc = dc,
                dmc = dmc, dhc = dhc, d3c = d3c)
    print(obj)
    saveRDS(obj, file = paste("resobj", dim, nopp, "RDS", sep = "."))
  }
}

dc <- run_playoff(100,  44, 20000, 30, 1, "")
# dexbot.config is the best for HU on all map sizes it seems




# 1620  380   up2date master
# 1685  315   moveresolve

# dexbot.config
#  1p 40x40
#
#
# 4p 20x20
#   1   2   3   4
# 436  54  63 327

# dexbot.multiway.config
#   4p 20x20
#   1   2   3   4
# 580  66  64 222
#   3p 30x30
#   1   2   3
# 164 244 593
#  3p 25x25
#   1   2   3   4
# 548  98  89 265
#
#  1p 40x40
#   1   2
# 365 636
#
halite -d "25 26" "python3 ReferenceBot.py" "python3 MyBot.py dexbot.mult"
