library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")
library("gbm")


MAX_TIME <- 0.94
TIME_CHECK_FREQUENCY <- 10
SPLASH_VALUE_MULTIPLIER <- 1.0

STAY_VALUE_RANGE <- seq(0.01, 3.01, by = 0.01)
MAX_STAY_RANGE <- seq(30, 240, by = 10)
ENEMY_PROD_RANGE <- seq(0.5, 3.5, by = 0.1)


sample_new_config <- function() {
  list(
    max_time = MAX_TIME,
    time_check_frequency = TIME_CHECK_FREQUENCY,
    splash_value_multiplier = SPLASH_VALUE_MULTIPLIER,
    stay_value_multiplier = sample(STAY_VALUE_RANGE, 1),
    max_stay_strength = sample(MAX_STAY_RANGE, 1),
    enemy_production_multiplier = sample(ENEMY_PROD_RANGE, 1)
  )
}

run_one_iter <- function() {
  sample_conf <- sample_new_config()

  toJSON(sample_conf, auto_unbox = TRUE) %>%
    cat(file = "dexbot.config")

  winner <- system("make run", intern = TRUE) %>%
    paste(collapse = "\n") %>%
    str_extract("(?<=, ).+(?=, came in rank #1!)")

  dt <- as.data.frame(sample_conf)
  dt$dexwins <- as.numeric(winner == "DexBot")
  dt
}


# Run nrun randomly sampled configs against RefBot ---------------------------
nrun <- 444
ncore <- 2

registerDoMC(ncore)
results <- foreach(i = seq(nrun), .combine = rbind) %dopar% {
  cat(".")
  run_one_iter()
}

# Fit GBM to the results and find optimal ------------------------------------
model <- gbm(dexwins ~ stay_value_multiplier + max_stay_strength + enemy_production_multiplier,
             distribution = "bernoulli",
             data = results,
             n.trees = 4000,
             n.minobsinnode = 5,
             train.fraction = 1.0,
             interaction.depth = 2,
             cv.folds = 10)

candidate <- expand.grid(stay_value_multiplier = STAY_VALUE_RANGE,
                         max_stay_strength = MAX_STAY_RANGE,
                         enemy_production_multiplier = ENEMY_PROD_RANGE)
candidate$prediction <- predict(model, newdata = candidate,
                                n.trees = gbm.perf(model),
                                type = "response")

candidate[order(candidate$prediction, decreasing = TRUE), ] %>% head
