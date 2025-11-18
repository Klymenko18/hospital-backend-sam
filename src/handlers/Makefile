.RECIPEPREFIX := >
.PHONY: build-MeRecordFunction build-AdminMetricsFunction build-HealthFunction build-DashboardFunction

_copy:
> mkdir -p $(ARTIFACTS_DIR)
> rsync -a --delete --exclude '__pycache__' ./ $(ARTIFACTS_DIR)/ 2>/dev/null || cp -a . $(ARTIFACTS_DIR)/

build-MeRecordFunction: _copy
build-AdminMetricsFunction: _copy
build-HealthFunction: _copy
build-DashboardFunction: _copy
