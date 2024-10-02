# import argparse
# import os
# import warnings
# import numpy as np
# # import torch
# # import torch.nn as nn
# # import torch.nn.functional as F
# # from torch.optim import Adam
# from sklearn.cluster import KMeans
# from sklearn.manifold import TSNE
# from sklearn.metrics.cluster import normalized_mutual_info_score as nmi_score

# from decomposition_plan_generation.multi_view_graph_clustering.utils import load_data, normalize_weight, bundled_label2origin, get_n_clusters, calculate_modularity
# from decomposition_plan_generation.multi_view_graph_clustering.models import EnDecoder, DuaLGR, GNN


# def DuaLGR_main(n_clusters, code_element_cnt, blocks, bundled_cousage, bundled_semantic, original_edges):
#     os.environ["OMP_NUM_THREADS"] = "3"
#     warnings.filterwarnings("ignore", category=UserWarning, message="KMeans is known to have a memory leak")
#     test_cnt = 1

#     # # hyperparameters settings
#     # parser = argparse.ArgumentParser()
#     # parser.add_argument('--quantize', type=float, default=0.8, help='quantize Omega')
#     # parser.add_argument('--varepsilon', type=float, default=0.3, help='varepsilon')
#     # parser.add_argument('--weight_soft', type=int, default=3, help='smooth-sharp paramter')
#     # parser.add_argument('--alpha', type=int, default=1, help='alpha')
#     # parser.add_argument('--endecoder_hidden_dim', type=int, default=512, help='endecoder_hidden_dim')
#     # parser.add_argument('--hidden_dim', type=int, default=512, help='hidden_dim')
#     # parser.add_argument('--latent_dim', type=int, default=128, help='latent_dim')
#     # parser.add_argument('--endecoder_lr', type=float, default=5e-4, help='learning rate for autoencoder')
#     # parser.add_argument('--lr', type=float, default=1e-3, help='learning rate for DuaLGR')
#     # parser.add_argument('--dataset', type=str, default='dblp', help='datasets: acm, dblp, texas, chameleon, acm00, acm01, acm02, acm03, acm04, acm05')
#     # parser.add_argument('--train', type=bool, default=True, help='training mode')
#     # parser.add_argument('--cuda_device', type=int, default=0, help='')
#     # parser.add_argument('--use_cuda', type=bool, default=False, help='')
#     # parser.add_argument('--file', type=str, default='fontforge-6_fontforge_merge_h', help='')
#     # parser.add_argument('--model_name', type=str, default='DuaLGR_dblp', help='model_name')
#     # parser.add_argument('--path', type=str, default='./data/', help='The path of datasets')
#     # parser.add_argument('--pretrain', type=int, default=500, help='pretrain epochs')
#     # parser.add_argument('--epoch', type=int, default=2000, help='')
#     # parser.add_argument('--patience', type=int, default=50, help='')
#     # parser.add_argument('--endecoder_weight_decay', type=float, default=1e-6, help='weight decay for autoencoder')
#     # parser.add_argument('--weight_decay', type=float, default=1e-4, help='weight decay for DuaLGR')
#     # parser.add_argument('--update_interval', type=int, default=10, help='')
#     # parser.add_argument('--random_seed', type=int, default=2023, help='')
#     # parser.add_argument('--n_clusters', type=int, default=n_clusters, help='number of clusters')
#     # args = parser.parse_args()


#     train = True
#     cuda_device = 0
#     use_cuda = torch.cuda.is_available()
#     weight_soft = 3
#     alpha = 1
#     quantize = 0.8
#     varepsilon = 0.3
#     endecoder_hidden_dim = 512
#     hidden_dim = 512
#     latent_dim = 128
#     pretrain = 500
#     epoch = 2000
#     patience = 50
#     endecoder_lr = 5e-4
#     endecoder_weight_decay = 1e-6
#     lr = 1e-3
#     weight_decay = 1e-4
#     update_interval = 10
#     random_seed = 2023
#     torch.manual_seed(random_seed)


#     labels, adjs_labels, shared_feature, shared_feature_label, graph_num = load_data(bundled_cousage, bundled_semantic)
#     N = code_element_cnt

#     print('nodes: {}'.format(shared_feature_label.shape[0]))
#     print('features: {}'.format(shared_feature_label.shape[1]))
#     print('class: {}'.format(labels.max() + 1))
#     print('N: {}'.format(N))

#     feat_dim = shared_feature.shape[1]
#     class_num = n_clusters
#     # y = labels.cpu().numpy()

#     endecoder = EnDecoder(feat_dim, endecoder_hidden_dim, class_num)
#     model = DuaLGR(feat_dim, hidden_dim, latent_dim, endecoder, class_num=class_num, num_view=graph_num)

#     if use_cuda:
#         torch.cuda.set_device(cuda_device)
#         torch.cuda.manual_seed(random_seed)
#         endecoder = endecoder.cuda()
#         model = model.cuda()
#         adjs_labels = [adj_labels.cuda() for adj_labels in adjs_labels]
#         shared_feature = shared_feature.cuda()
#         shared_feature_label = shared_feature_label.cuda()
#     device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

#     if train:
#         # =============================================== pretrain endecoder ============================
#         kmeans = KMeans(n_clusters=class_num, n_init=5)
#         y_pred = kmeans.fit_predict(shared_feature_label.data.cpu().numpy())

#         optimizer_endecoder = Adam(endecoder.parameters(), lr=endecoder_lr, weight_decay=endecoder_weight_decay)

#         for epoch_num in range(pretrain):
#             endecoder.train()
#             loss_re = 0.
#             loss_a = 0.

#             a_pred, x_pred, z_norm = endecoder(shared_feature)
#             for v in range(graph_num):
#                 loss_a += F.binary_cross_entropy(a_pred, adjs_labels[v])
#             loss_re += F.binary_cross_entropy(x_pred, shared_feature_label)

#             loss = loss_re + loss_a
#             optimizer_endecoder.zero_grad()
#             loss.backward()
#             optimizer_endecoder.step()
#             # print('epoch: {}, loss:{}, loss_re:{}, loss_a: {}'.format(epoch_num, loss, loss_re, loss_a))

#             if epoch_num == pretrain - 1:
#                 print('Pretrain complete...')
#                 kmeans = KMeans(n_clusters=class_num, n_init=5)
#                 y_pred = kmeans.fit_predict(z_norm.data.cpu().numpy())
#                 break


#         # =========================================Train=============================================================
#         print('Begin trains...')
#         param_all = []
#         for v in range(graph_num+1):
#             param_all.append({'params': model.cluster_layer[v]})
#         param_all.append({'params': model.gnn.parameters()})
#         optimizer_model = Adam(param_all, lr=lr, weight_decay=weight_decay)

#         best_a = [1e-12 for i in range(graph_num)]
#         weights = normalize_weight(best_a)
#         # weights = np.load('../data/weights/' + file + '.npy', allow_pickle=True)

#         with torch.no_grad():
#             model.eval()
#             pseudo_label = y_pred
#             a_pred, x_pred, z_all, q_all, a_pred_x, x_pred_x = model(shared_feature, adjs_labels, weights, pseudo_label, alpha, quantize=quantize, varepsilon=varepsilon)
#             kmeans = KMeans(n_clusters=class_num, n_init=5)
#             for v in range(graph_num+1):
#                 y_pred = kmeans.fit_predict(z_all[v].data.cpu().numpy())
#                 model.cluster_layer[v].data = torch.tensor(kmeans.cluster_centers_).to(device)
#                 # eva(y, y_pred, 'K{}'.format(v))
#             pseudo_label = y_pred

#         bad_count = 0
#         best_epoch = 0
#         best_modularity = 0
#         best_result = []

#         loss_list = []
#         modularity_list = []
#         for epoch_num in range(epoch):
#             model.train()

#             loss_re = 0.
#             loss_kl = 0.
#             loss_re_a = 0.
#             loss_re_ax = 0.

#             a_pred, x_pred, z_all, q_all, a_pred_x, x_pred_x = model(shared_feature, adjs_labels, weights, pseudo_label, alpha, quantize=quantize, varepsilon=varepsilon)
#             for v in range(graph_num):
#                 loss_re_a += F.binary_cross_entropy(a_pred, adjs_labels[v])
#             loss_re_x = F.binary_cross_entropy(x_pred, shared_feature_label)
#             loss_re += loss_re_a + loss_re_x

#             kmeans = KMeans(n_clusters=class_num, n_init=5)
#             y_prim = kmeans.fit_predict(z_all[-1].detach().cpu().numpy())
#             pseudo_label = y_prim
#             views = []

#             for v in range(graph_num):
#                 y_pred = kmeans.fit_predict(z_all[v].detach().cpu().numpy())
#                 views.append(z_all[v].detach().cpu().numpy())
#                 a = nmi_score(bundled_label2origin(blocks, y_prim, N), bundled_label2origin(blocks, y_pred, N))
#                 best_a[v] = a

#             weights = normalize_weight(best_a, p=weight_soft)
#             # weights = pca_weights(views)
#             # print(weights)

#             p = model.target_distribution(q_all[-1])
#             for v in range(graph_num):
#                 loss_kl += F.kl_div(q_all[v].log(), p, reduction='batchmean')
#             loss_kl += F.kl_div(q_all[-1].log(), p, reduction='batchmean')

#             loss = loss_re + loss_kl
#             loss_list.append(loss.item())
#             optimizer_model.zero_grad()
#             loss.backward()
#             optimizer_model.step()

#             # print('epoch: {}, loss: {}, loss_re: {}, loss_kl:{}, badcount: {}, loss_re_a: {}, loss_re_x: {}'. format(epoch_num, loss, loss_re, loss_kl, bad_count, loss_re_a, loss_re_x))

#         # =========================================evaluation=============================================================
#             if epoch_num % update_interval == 0:
#                 model.eval()
#                 with torch.no_grad():
#                     a_pred, x_pred, z_all, q_all, a_pred_x, x_pred_x = model(shared_feature, adjs_labels, weights, pseudo_label, alpha, quantize=quantize, varepsilon=varepsilon)
#                     kmeans = KMeans(n_clusters=class_num, n_init=5)
#                     y_eval = kmeans.fit_predict(z_all[-1].detach().cpu().numpy())
#                     modularity = calculate_modularity(bundled_label2origin(blocks, y_eval, N), original_edges)
#                     modularity_list.append(modularity.item())
            
            
#                 if modularity > best_modularity:
#                     best_modularity = modularity
#                     best_epoch = epoch_numA
#                     bad_count = 0
#                     best_result = bundled_label2origin(blocks, y_eval, N)
#                     print('epoch: {}, best modularity:{}, count: {}'.format(best_epoch, best_modularity, test_cnt))
#                     test_cnt += 1
#                 else:
#                     bad_count += 1
#                     print('epoch: {}, best modularity:{}, bad_count: {}'.format(epoch_num, best_modularity, bad_count))

#                 if bad_count >= patience:
#                     print('complete training, best modularity:{}, bestepoch:{}\n'.format(best_modularity, best_epoch))
#                     print()
#                     break
    
#     return best_result
    


    