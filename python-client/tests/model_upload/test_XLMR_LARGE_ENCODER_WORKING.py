from giskard.client.project import GiskardProject
import torchtext
from torchtext.functional import to_tensor
import pytest

@pytest.mark.skip(reason="Will be solved in the new API: https://github.com/Giskard-AI/giskard/pull/618")
def test_XLMR_LARGE_ENCODER():

    xlmr_large = torchtext.models.XLMR_LARGE_ENCODER
    classifier_head = torchtext.models.RobertaClassificationHead(num_classes=2, input_dim = 1024)
    model = xlmr_large.get_model(head=classifier_head)
    transform = xlmr_large.transform()
    #input_batch = ["Hello world", "How are you!"]
    #df = pd.DataFrame(input_batch,columns=['text'])
    def prediction_function(df):
        input_batch = df['text'].values.tolist()
        model_input = to_tensor(transform(input_batch), padding_value=1)
        output = model(model_input)
        return output.cpu().detach().numpy()

    GiskardProject._validate_model_is_pickleable(prediction_function)