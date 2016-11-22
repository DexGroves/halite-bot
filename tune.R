library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")
library("gbm")


MAX_TIME <- 0.94
TIME_CHECK_FREQUENCY <- 10

SPLASH_VALUE_MULTIPLIER <- seq(0.8, 1.1, by = 0.1)
STAY_VALUE_RANGE <- seq(2.50, 2.75, by = 0.01)
MAX_STAY_RANGE <- seq(90, 110, by = 1)
ENEMY_PROD_RANGE <- seq(1.15, 1.25, by = 0.01)
CAP_AVOIDANCE_RANGE <- c(4900, 5000)  # seq(-100, 300, by = 10)
FALLOFF_EXPONENT_RANGE <- seq(1.75, 1.85, by = 0.01)
STR_PENALTY_RANGE <- seq(0, 0.1, by = 0.01)
OPPONENT_RANGE <- c(1)
DIM_RANGE <- c(20, 25, 30, 35)
EXCLUDE_RANGE <- c(TRUE, TRUE)

sample_new_config <- function(N = 1) {
  list(
    max_time = rep(MAX_TIME, N),
    time_check_frequency = rep(TIME_CHECK_FREQUENCY, N),
    splash_value_multiplier = sample(SPLASH_VALUE_MULTIPLIER, N, TRUE),
    stay_value_multiplier = sample(STAY_VALUE_RANGE, N, TRUE),
    max_stay_strength = sample(MAX_STAY_RANGE, N, TRUE),
    enemy_production_multiplier = sample(ENEMY_PROD_RANGE, N, TRUE),
    cap_avoidance = sample(CAP_AVOIDANCE_RANGE, N, TRUE),
    falloff_exponent = sample(FALLOFF_EXPONENT_RANGE, N, TRUE),
    exclude_str = sample(EXCLUDE_RANGE, N, TRUE),
    str_penalty = sample(STR_PENALTY_RANGE, N, TRUE),
    nopp = sample(OPPONENT_RANGE, N, TRUE),
    dim = sample(DIM_RANGE, N, TRUE)
  )
}

run_one_iter <- function() {
  sample_conf <- sample_new_config()

  toJSON(sample_conf, auto_unbox = TRUE) %>%
    cat(file = "dexbot.config")

  bot_placement <- build_call(sample_conf$dim, sample_conf$nopp) %>%
    system(intern = TRUE) %>%
    paste(collapse = "\n") %>%
    str_extract("(?<=DexBot, came in rank #)[0-9]")

  dt <- as.data.frame(sample_conf)

  dt$dexrank <- 1 - ((as.numeric(bot_placement) - 1) / (sample_conf$nopp))

  dt
}

build_call <- function(dim, nopp) {
  call <- paste0(
    "halite -d ",
    "\"", dim, " ", dim, "\" ",
    "\"python3 MyBot.py\" ",
    paste(rep("\"python3 ReferenceBot.py\"", nopp), collapse = " ")
  )
  call
}

# Run nrun randomly sampled configs against RefBot ---------------------------
nrun <- 5000
ncore <- 12

registerDoMC(ncore)
results <- foreach(i = seq(nrun), .combine = rbind) %dopar% {
  if (i %% 10 == 0) {
    cat(paste(i, "\n"))
  }
  run_one_iter()
}

# Fit GBM to the results and find optimal ------------------------------------
results$exclude_str <- as.numeric(results$exclude_str)
model <- gbm(dexrank ~ stay_value_multiplier + max_stay_strength + enemy_production_multiplier + cap_avoidance + falloff_exponent + str_penalty,
             distribution = "bernoulli",
             data = results[!is.na(results$dexrank), ],
             n.trees = 5000,
             n.minobsinnode = 5,
             train.fraction = 1.0,
             interaction.depth = 3,
             cv.folds = 10,
             n.cores = 11)

newdata <- as.data.frame(sample_new_config(1000000))
newdata$exclude_str <- as.numeric(newdata$exclude_str)

newdata$mpred <- predict(model, newdata = newdata, n.trees = gbm.perf(model))
newdata[order(newdata$mpred), ] %>% tail
plot(model, 6, return.grid = TRUE)
summary(model)



# candidate <- expand.grid(stay_value_multiplier = STAY_VALUE_RANGE,
#                          max_stay_strength = MAX_STAY_RANGE,
#                          enemy_production_multiplier = ENEMY_PROD_RANGE)
# candidate$prediction <- predict(model, newdata = candidate,
#                                 n.trees = gbm.perf(model),
#                                 type = "response")

# candidate[order(candidate$prediction, decreasing = TRUE), ] %>% head
