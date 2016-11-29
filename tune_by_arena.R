library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

epm_range =               seq(0.7, 1.3, length.out = 100)
bsm_range =               seq(-0.02, -0.2, length.out = 100)
esm_range =               seq(-0.002, -0.2, length.out = 100)
eprox_range =             seq(0.05, 0.25, length.out = 100)
bprox_range =             seq(0.5, 1.5, length.out = 100)
splash_range =            seq(0.001, 0.05, length.out = 100)
stay_val_range =          seq(0.8, 1.5, length.out = 100)
max_edge_str_range =      seq(300, 400, length.out = 100)
max_stay_strn_range =     seq(25, 75, length.out = 100)
falloff_range =           seq(1.8, 2.2, length.out = 100)
border_cutoff_range =     seq(45, 65, length.out = 100)
stay_border_bonus_range = seq(0, 0.1, length.out = 100)
min_wait_turns_range =    seq(2,7)

earlygame_max_t_range =      seq(12,48)
earlygame_order_range =      seq(4,7)
earlygame_max_area_range =   seq(4,16)
earlygame_decay_range =      c(TRUE, FALSE)
earlygame_all_border_range = c(TRUE, FALSE)

sample_new_config <- function(N = 1) {
  list(
    epm =           sample(epm_range, N, TRUE),
    bsm =           sample(bsm_range, N, TRUE),
    esm =           sample(esm_range, N, TRUE),
    eprox =         sample(eprox_range, N, TRUE),
    bprox =         sample(bprox_range, N, TRUE),
    splash =        sample(splash_range, N, TRUE),
    stay_val =      sample(stay_val_range, N, TRUE),
    max_edge_str =  sample(max_edge_str_range, N, TRUE),
    max_stay_strn = sample(max_stay_strn_range, N, TRUE),
    falloff =       sample(falloff_range, N, TRUE),
    border_cutoff = sample(border_cutoff_range, N, TRUE),
    stay_border_bonus = sample(stay_border_bonus_range, N, TRUE),
    earlygame_max_t = sample(earlygame_max_t_range, N, TRUE),
    earlygame_order = sample(earlygame_order_range, N, TRUE),
    earlygame_max_area = sample(earlygame_max_area_range, N, TRUE),
    earlygame_decay = sample(earlygame_decay_range, N, TRUE),
    earlygame_all_border = sample(earlygame_all_border_range, N, TRUE),
    min_wait_turns = sample(min_wait_turns_range, N, TRUE),
    name = paste0("DexBot_", seq(N))
  )
}

build_call <- function(dim, configs) {
  config_args <- paste(paste("\"python3 MyBot.py", configs, "\" "),
                       collapse = " ")
  call <- paste0(
    "halite -t -d ",
    "\"", dim, " ", dim, "\" ",
    config_args
  )
  call
}

# 11s per conf-core
nplayers <- 4
nrounds <- 5
ngame_r1 <- 18
dim <- 20
ncore <- 36

nconfs <- nplayers ^ nrounds

configs <- as.data.frame(sample_new_config(nconfs))
configs$ave_placement <- 0
configs$agg_placement <- 0

for (j in seq(nrow(configs))) {
  cat(j)
  cat("\t")
  as.list(configs[j, ]) %>%
    toJSON(auto_unbox = TRUE, prettify = TRUE) %>%
    cat(file = as.character(configs[j, "name"]))
}

system.time({
registerDoMC(ncore)
for (round in seq(nrounds-1)) {
  cat(paste("ROUND", round, "\n"))

  round_runs <- max(ncore, ngame_r1 * 2 ^ (round - 1))
  for (i in seq(nrow(configs) / nplayers)) {
    min_conf <- (i-1)*nplayers + 1
    max_conf <- (i) * nplayers
    this_confs <- configs[seq(min_conf, max_conf), ]

    cat(paste("\n\tConf. nbr", i, "of", nrow(configs) / nplayers, "\n"))
    call <- build_call(dim, as.character(this_confs$name))
    results <- foreach(i = seq(round_runs), .combine = rbind) %dopar% {
      cat(".")
      system(call, intern = TRUE) %>%
        tail(nplayers) %>%
        sapply(str_extract, "(?<=came in rank #)[0-9]") %>%
        as.numeric
    }
    system("rm *.hlt")
    res <- apply(results, 2, mean)
    configs[seq(min_conf, max_conf),
            "ave_placement"] <- res
    configs[seq(min_conf, max_conf),
            "agg_placement"] <- sapply(seq(nplayers),
                                       function(x) which(order(res) == x))

  }
  saveRDS(configs, file="confs.RDS")
  configs <- configs[configs$agg_placement == 1, ]
}
})
test <- readRDS(configs, file="confs.RDS")
#            epm        bsm    esm      eprox     bprox     splash  stay_val max_edge_str max_stay_strn  falloff border_cutoff stay_border_bonus
# 138  1.1787879 -0.1563636 -0.150 0.08232323 0.9141414 0.04604040 1.1818182     356.5657      44.69697 1.973737      48.63636       0.053535354
# 286  1.1666667 -0.1290909 -0.032 0.25000000 0.6414141 0.01386869 0.8777778     319.1919      59.84848 1.929293      46.41414       0.067676768
# 746  0.7181818 -0.1436364 -0.196 0.09646465 0.9242424 0.01535354 1.1606061     328.2828      65.40404 2.070707      64.59596       0.060606061
# 1022 0.9060606 -0.1054545 -0.062 0.17121212 0.8838384 0.02277778 0.8141414     387.8788      64.89899 1.981818      57.32323       0.005050505
#      earlygame_max_t earlygame_order earlygame_max_area earlygame_decay earlygame_all_border min_wait_turns        name ave_placement agg_placement
# 138               19               5                  8           FALSE                FALSE              2  DexBot_138      2.319444             1
# 286               32               7                  9           FALSE                FALSE              4  DexBot_286      2.173611             1
# 746               44               4                 13            TRUE                FALSE              3  DexBot_746      2.347222             1
# 1022              16               5                 10           FALSE                FALSE              5 DexBot_1022      2.326389             1

this_confs <- configs

call <- build_call(dim, as.character(this_confs$name))
results <- foreach(i = seq(4000), .combine = rbind) %dopar% {
  cat(".")
  system(call, intern = TRUE) %>%
    tail(nplayers) %>%
    sapply(str_extract, "(?<=came in rank #)[0-9]") %>%
    as.numeric
}
apply(results, 2, mean)
system("rm *.hlt")
res <- apply(results, 2, mean)
configs <- configs[1:4]
configs["ave_placement", ] <- res
configs["agg_placement", ] <- sapply(seq(nplayers),
                                   function(x) which(order(res) == x))

}
