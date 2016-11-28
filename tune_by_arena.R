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
    "halite -d ",
    "\"", dim, " ", dim, "\" ",
    config_args
  )
  call
}


nplayers <- 5
nrounds <- 5
ngame_r1 <- 24
dim <- 30
ncore <- 52

nconfs <- nplayers ^ nrounds

configs <- as.data.frame(sample_new_config(nconfs))
configs$ave_placement <- 0
configs$agg_placement <- 0

registerDoMC(ncore)
for (round in seq(nrounds-1)) {
  cat(paste("ROUND", round, "\n"))

  round_runs <- max(ncore, ngame_r1 * 2 ^ (round - 1))
  for (i in seq(nrow(configs) / nplayers)) {
    min_conf <- (i-1)*nplayers + 1
    max_conf <- (i) * nplayers
    this_confs <- configs[seq(min_conf, max_conf), ]

    for (j in nrow(this_confs)) {
      as.list(this_confs[j, ]) %>%
        toJSON(auto_unbox = TRUE, prettify = TRUE) %>%
        cat(file = as.character(this_confs[j, "name"]))
    }
    cat(paste("\tConf. nbr", i, "\n"))
    call <- build_call(dim, this_confs$name)
    results <- foreach(i = seq(round_runs), .combine = rbind) %dopar% {
      cat(".")
      system(call, intern = TRUE) %>%
        tail(nplayers) %>%
        sapply(str_extract, "(?<=came in rank #)[0-9]") %>%
        as.numeric
    }
    system("rm *.hlt")
    configs[seq(min_conf, max_conf),
            "ave_placement"] <- apply(results, 2, mean)
    configs[seq(min_conf, max_conf),
            "agg_placement"] <- order(apply(results, 2, mean))
  }

  configs <- configs[configs$agg_placement == 1, ]
}
