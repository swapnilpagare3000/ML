import {DatasetDTO, JobDTO, ModelDTO, TestFunctionDTO, TestSuiteDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {defineStore} from 'pinia';
import {api} from '@/api';
import {chain} from 'lodash';
import {trackJob} from '@/utils/job-utils';
import {useMainStore} from '@/stores/main';
import mixpanel from 'mixpanel-browser';

interface State {
    projectId: number | null,
    inputs: { [name: string]: string },
    suite: TestSuiteDTO | null,
    registry: TestFunctionDTO[],
    datasets: { [key: string]: DatasetDTO },
    models: { [key: string]: ModelDTO },
    executions: TestSuiteExecutionDTO[],
    trackedJobs: { [uuid: string]: JobDTO }
}

const mainStore = useMainStore();

export const useTestSuiteStore = defineStore('testSuite', {
    state: (): State => ({
        projectId: null,
        inputs: {},
        suite: null,
        registry: [],
        datasets: {},
        models: {},
        executions: [],
        trackedJobs: {}
    }),
    getters: {
        suiteId: ({suite}) => suite === null ? null : suite.id,
        testSuiteResults: ({executions}) => {
            if (!executions) {
                return {};
            }

            return chain(executions)
                .map(execution => (execution.results ?? []).map(
                    result => ({
                        testResult: result,
                        testSuiteResult: execution
                    })
                ))
                .flatten()
                .groupBy(result => result.testResult.test.testUuid)
                .value();
        }
    },
    actions: {
        async reload() {
            if (this.suiteId !== null && this.projectId !== null) {
                await this.loadTestSuite(this.projectId, this.suiteId!)
            }
        },
        async loadTestSuite(projectId: number, suiteId: number) {
            const completeSuite = await api.getTestSuiteComplete(projectId, suiteId);

            this.projectId = projectId;
            this.inputs = completeSuite.inputs;
            this.suite = completeSuite.suite;
            this.registry = completeSuite.registry;
            this.datasets = Object.fromEntries(completeSuite.datasets.map(x => [x.id, x]));
            this.models = Object.fromEntries(completeSuite.models.map(x => [x.id, x]));
            this.executions = completeSuite.executions;
        },
        async updateTestSuite(projectKey: string, testSuite: TestSuiteDTO) {
            mixpanel.track('Update test suite v2', {
                projectKey
            });

            this.suite = await api.updateTestSuite(projectKey, testSuite);
        },
        async trackJob(uuid: string) {
            console.log(uuid);
            const result = await trackJob(uuid, (res) => this.trackedJobs = {
                ...this.trackedJobs,
                [uuid]: res
            });

            const res = {...this.trackedJobs};
            delete res[uuid]
            this.trackedJobs = res;

            if (result) {
                mainStore.addNotification({
                    content: 'Test suite execution has been executed successfully',
                    color: 'success'
                });
            } else {
                mainStore.addNotification({
                    content: 'An error has happened during the test suite execution',
                    color: 'error'
                });
            }

            await this.reload();
        }
    }
});
