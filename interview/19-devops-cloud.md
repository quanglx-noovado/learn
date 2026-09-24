# 19. DevOps và Cloud

> [← Mục lục](README.md) · Phạm vi: Docker, Kubernetes, CI/CD, chiến lược deploy và migration,
> IaC, dịch vụ cloud (AWS làm ví dụ), môi trường, config, chi phí.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

Observability (log, metric, trace, alert) và xử lý sự cố nằm ở
[18-reliability-observability.md](18-reliability-observability.md). Kiến thức Linux nền (signal,
PID 1, cgroup) ở [01-os-linux.md](01-os-linux.md).

## Bản đồ nhanh

**Docker**
- [ ] 🟢 Image và container; container và VM
- [ ] 🟢 Layer, build cache, thứ tự lệnh
- [ ] 🟢 Multi-stage build, image nhỏ, image base
- [ ] 🟡 Non-root, `.dockerignore`, không nhét secret vào image
- [ ] 🟡 `ENTRYPOINT` và `CMD`, exec form và shell form
- [ ] 🟡 `HEALTHCHECK`
- [ ] 🟢 Volume, network, `docker compose` cho môi trường dev
- [ ] 🟢 ⚠️ Container là tạm thời, dữ liệu phải ở volume hoặc dịch vụ ngoài
- [ ] 🔴 Tag bất biến, digest, scan image, SBOM

**Kubernetes**
- [ ] 🟡 Pod, ReplicaSet, Deployment
- [ ] 🟡 Service: ClusterIP, NodePort, LoadBalancer; Ingress
- [ ] 🟡 ConfigMap, Secret
- [ ] 🟡 Liveness, readiness, startup probe và cạm bẫy
- [ ] 🟡 Resource request/limit, QoS class
- [ ] 🟡 HPA
- [ ] 🟡 Rolling update: `maxSurge`, `maxUnavailable`
- [ ] 🔴 PodDisruptionBudget
- [ ] 🔴 StatefulSet
- [ ] 🟡 Job, CronJob
- [ ] 🔴 Graceful shutdown trong Kubernetes: preStop, endpoint propagation
- [ ] 🟡 Namespace, RBAC, Helm/Kustomize ở mức biết dùng

**CI/CD**
- [ ] 🟢 Pipeline: lint, test, build, scan, deploy
- [ ] 🟡 Artifact: build một lần, deploy nhiều môi trường
- [ ] 🟡 Cache trong CI
- [ ] 🟡 Secret trong CI, OIDC
- [ ] 🟡 Quality gate

**Deploy**
- [ ] 🟢 Rolling, blue-green, canary; cách rollback mỗi loại
- [ ] 🟢 Feature flag: tách deploy khỏi release
- [ ] 🟡 Rollback: code, config, data
- [ ] 🔴 Database migration khi deploy: expand/contract
- [ ] 🟡 Zero-downtime: graceful shutdown, readiness, migration tương thích ngược

**IaC và GitOps**
- [ ] 🟡 Terraform: state, plan/apply, drift, module, locking
- [ ] 🟡 Ansible đại ý
- [ ] 🔴 GitOps, Argo CD đại ý

**Cloud (AWS làm ví dụ)**
- [ ] 🟡 Compute: EC2, ECS/EKS, Lambda
- [ ] 🟡 Storage và DB: S3, RDS/Aurora, DynamoDB, ElastiCache
- [ ] 🟡 Messaging: SQS, SNS
- [ ] 🟡 Edge: CloudFront, Route 53
- [ ] 🟡 IAM: least privilege, role và user
- [ ] 🟡 VPC, CloudWatch
- [ ] 🔴 Serverless trade-off: cold start, giới hạn thời gian, concurrency
- [ ] 🟡 Region, AZ, multi-AZ

**Môi trường và vận hành**
- [ ] 🟢 dev, staging, production; ⚠️ staging khác production thì bug vẫn lọt
- [ ] 🟡 12-factor app
- [ ] 🟡 Quản lý config và secret
- [ ] 🔴 Cost awareness

## Chi tiết

### Docker

- [ ] Image, container, VM 🟢
  - Image: template chỉ đọc gồm nhiều layer. Container: process chạy từ image, thêm một layer
    ghi được (mất khi xoá container)
  - Container không phải VM: dùng chung kernel của host, cô lập bằng namespace (PID, network,
    mount, user...) và giới hạn bằng cgroup. Khởi động nhanh, nhẹ, nhưng cô lập yếu hơn VM
  - VM có kernel riêng trên hypervisor: cô lập mạnh, nặng hơn. Microvm (Firecracker, dùng bởi
    Lambda/Fargate) là điểm giữa
  - ⚠️ Container Linux trên macOS/Windows thực ra chạy trong một VM Linux → hiệu năng file mount
    khác production
- [ ] Layer và build cache 🟢
  - Mỗi lệnh `RUN`, `COPY`, `ADD` tạo một layer. Layer nào đổi thì mọi layer sau build lại
  - Quy tắc: thứ ít đổi đặt trước. Copy file khai báo dependency, cài dependency, rồi mới copy
    source code
  - ⚠️ Xoá file ở layer sau không làm image nhỏ đi: file vẫn nằm trong layer trước. Cài và dọn
    phải cùng một `RUN`
  - BuildKit: `RUN --mount=type=cache` giữ cache của package manager giữa các lần build;
    `--mount=type=secret` dùng secret lúc build mà không lưu vào layer
- [ ] Multi-stage build và image nhỏ 🟢
  - Stage build có compiler, dev dependency; stage cuối chỉ copy artifact cần chạy
  - Image base: `distroless`, `alpine`, `-slim`, hoặc `scratch` (Go binary tĩnh)
  - ⚠️ Alpine dùng musl thay glibc: khác biệt về DNS resolver, hiệu năng, extension native
    (Python wheel, một số extension PHP) → đôi khi `-slim` (Debian) ít rắc rối hơn
  - Image nhỏ: pull nhanh (scale nhanh), ít CVE. Distroless không có shell → debug bằng
    ephemeral container (`kubectl debug`)

```dockerfile
FROM golang:1.26 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/app ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/app /app
USER nonroot
ENTRYPOINT ["/app"]
```

- [ ] Non-root, `.dockerignore`, secret 🟡
  - Mặc định container chạy root (UID 0, cùng UID root của host nếu không có user namespace). Lỗ
    hổng thoát container sẽ nguy hiểm hơn nhiều → `USER` không phải root, file system chỉ đọc
    nếu được
  - ⚠️ Non-root có thể không bind được port < 1024 (tuỳ runtime, kiểm tra lại) → quen listen 8080
  - `.dockerignore`: loại `.git`, `node_modules`, `vendor`, `.env`, log. Giảm build context,
    tránh cache bị vô hiệu, tránh lộ secret
  - ⚠️ `COPY . .` kèm `.env` → secret nằm trong image mãi mãi, ai pull được image đều đọc được.
    `ARG`/`ENV` chứa secret cũng lộ qua `docker history`/`inspect`
- [ ] `ENTRYPOINT` và `CMD` 🟡
  - `ENTRYPOINT` là chương trình chính; `CMD` là đối số mặc định (hoặc lệnh mặc định nếu không có
    ENTRYPOINT). `docker run image args` thay `CMD`, giữ `ENTRYPOINT`
  - Exec form `["app", "--flag"]`: chạy trực tiếp, app là PID 1, nhận signal
  - Shell form `app --flag`: chạy qua `/bin/sh -c`, shell là PID 1, ⚠️ SIGTERM không tới app →
    bị SIGKILL sau grace period (xem [01-os-linux.md](01-os-linux.md))
  - Entrypoint script thì kết thúc bằng `exec "$@"`
- [ ] `HEALTHCHECK` 🟡
  - Docker gọi lệnh định kỳ, đánh dấu container `healthy`/`unhealthy`; Docker Compose dùng được
    với `depends_on: condition: service_healthy`
  - ⚠️ Kubernetes bỏ qua `HEALTHCHECK` trong image; dùng probe của pod
- [ ] Volume, network, compose 🟢
  - Named volume (Docker quản lý) và bind mount (thư mục host). Dữ liệu DB trong dev phải nằm ở
    volume
  - Compose tạo network riêng, service gọi nhau bằng tên service
  - ⚠️ `depends_on` chỉ đảm bảo thứ tự khởi động, không đảm bảo service kia đã sẵn sàng
- [ ] Tag, digest, scan 🔴
  - ⚠️ `:latest` hoặc tag bị ghi đè → không biết đang chạy bản nào, rollback không chắc chắn.
    Tag theo git SHA hoặc version; production có thể pin theo digest `@sha256:...`
  - Scan CVE (Trivy, Grype, scanner của registry), SBOM, ký image (cosign) ở mức biết tên

### Kubernetes

- [ ] Pod, ReplicaSet, Deployment 🟡
  - Pod: đơn vị nhỏ nhất, một hoặc vài container chung network namespace (gọi nhau qua
    `localhost`) và volume. Pod là tạm thời, IP đổi khi tạo lại
  - ReplicaSet giữ đủ N pod. Deployment quản lý ReplicaSet để rolling update và rollback
    (`kubectl rollout undo`)
  - Sidecar: container phụ trong pod (proxy, log shipper); init container chạy trước app
- [ ] Service và Ingress 🟡

| Loại | Truy cập từ | Dùng khi |
|---|---|---|
| `ClusterIP` (mặc định) | trong cluster | service nội bộ |
| `NodePort` | `IP_node:port` (dải 30000–32767) | thử nghiệm, LB ngoài tự quản |
| `LoadBalancer` | LB của cloud | mở một service ra ngoài |
| Headless (`clusterIP: None`) | DNS trả IP từng pod | StatefulSet, client tự chọn pod |

  - Service chọn pod bằng label selector; chỉ pod **ready** mới vào danh sách endpoint
  - Ingress: rule L7 (host, path) → Service; cần ingress controller (Nginx ingress, Traefik,
    AWS Load Balancer Controller). Gateway API là thế hệ kế tiếp
  - ⚠️ Mỗi Service `LoadBalancer` là một LB cloud tính tiền → gom qua một Ingress
- [ ] ConfigMap và Secret 🟡
  - Đưa vào pod qua env var hoặc mount file
  - ⚠️ Secret chỉ là base64, không phải mã hoá. Cần bật encryption at rest cho etcd, RBAC chặt,
    hoặc dùng External Secrets / Secrets Store CSI với secret manager của cloud
  - ⚠️ Đổi ConfigMap không tự restart pod; env var chỉ đọc lúc khởi động. File mount được cập nhật
    sau một lúc, nhưng app phải tự đọc lại. Cách hay dùng: thêm hash config vào annotation của pod
    template để đổi config là rollout
- [ ] Probes 🟡

| Probe | Câu hỏi | Fail thì |
|---|---|---|
| startup | app khởi động xong chưa? | chờ; hết số lần thì restart. Liveness/readiness chưa chạy |
| readiness | có nhận traffic được không? | bị gỡ khỏi endpoint của Service, không restart |
| liveness | process có bị kẹt không, cần restart? | kubelet restart container |

  - ⚠️ Liveness kiểm tra DB/Redis/service khác: dependency chậm → mọi pod bị restart cùng lúc →
    sự cố nhỏ thành outage toàn bộ. Liveness chỉ nên kiểm tra chính process (deadlock, event loop
    đứng)
  - ⚠️ Readiness kiểm tra dependency chung cũng nguy hiểm: DB chậm → mọi pod not ready → 503 toàn
    bộ, kể cả endpoint không cần DB. Cân nhắc kỹ, thường chỉ kiểm tra thứ riêng của pod
  - ⚠️ Không có startup probe với app khởi động chậm (JVM, warm cache) → liveness giết app trước
    khi nó kịp lên → restart loop (`CrashLoopBackOff`)
  - ⚠️ Timeout probe quá ngắn khi app bận GC/CPU throttle → restart dưới tải, càng tệ hơn
  - Endpoint probe phải rẻ, không cần auth, không log mỗi lần gọi
- [ ] Resource request và limit 🟡
  - Request: scheduler dùng để xếp pod lên node, đảm bảo tối thiểu. Limit: trần
  - Vượt memory limit → OOMKilled. Vượt CPU limit → bị throttle (chậm, không bị kill)
  - QoS: `Guaranteed` (request = limit mọi container), `Burstable`, `BestEffort` (không đặt gì,
    bị evict đầu tiên khi node thiếu tài nguyên)
  - ⚠️ Không đặt request → scheduler xếp quá tay, node quá tải. Request quá cao → lãng phí tiền
  - Tranh luận CPU limit: nhiều team chỉ đặt CPU request, bỏ CPU limit để tránh throttle; memory
    thì nên đặt limit. Nói được cả hai phía
  - Runtime phải biết limit: JVM `MaxRAMPercentage`, Go `GOMEMLIMIT`/`GOMAXPROCS`
- [ ] HPA 🟡
  - Tự đổi số replica theo metric: CPU/memory so với **request** (không phải limit), hoặc custom
    metric (request/giây, độ dài queue qua KEDA)
  - ⚠️ Không đặt request thì HPA theo CPU không hoạt động
  - ⚠️ Scale mất thời gian (pull image, khởi động, warm up) → không cứu được spike vài giây. Giữ
    `minReplicas` đủ, image nhỏ, khởi động nhanh
  - ⚠️ Scale app mà DB không scale → nhiều pod hơn chỉ làm cạn connection DB nhanh hơn
  - Node autoscaling (Cluster Autoscaler, Karpenter) là lớp riêng; HPA thêm pod nhưng không có
    node trống thì pod `Pending`
- [ ] Rolling update 🟡
  - `maxSurge` (thêm tối đa bao nhiêu pod mới) và `maxUnavailable` (bớt tối đa bao nhiêu pod cũ),
    mặc định 25% mỗi cái
  - Pod mới phải ready mới tiếp tục → readiness probe quyết định tốc độ và độ an toàn
  - Trong lúc rollout, bản cũ và bản mới chạy song song → API, message format, schema DB phải
    tương thích hai chiều
- [ ] PodDisruptionBudget 🔴
  - Giới hạn số pod bị gián đoạn **tự nguyện** cùng lúc (drain node, nâng cấp cluster):
    `minAvailable` hoặc `maxUnavailable`
  - ⚠️ Không bảo vệ khỏi gián đoạn không tự nguyện (node chết, OOM)
  - ⚠️ PDB `minAvailable` bằng số replica → drain node treo mãi, chặn nâng cấp cluster
  - Kết hợp với anti-affinity/topology spread để replica không cùng node/AZ
- [ ] StatefulSet 🔴
  - Pod có tên và thứ tự ổn định (`db-0`, `db-1`), mỗi pod một PersistentVolume riêng giữ lại khi
    pod tạo lại, DNS ổn định qua headless Service; khởi động/tắt theo thứ tự
  - Dùng cho DB, Kafka, Elasticsearch. ⚠️ Tự chạy DB trên Kubernetes là tự gánh backup, failover,
    nâng cấp; nhiều team chọn managed DB (RDS) cho production
- [ ] Job và CronJob 🟡
  - Job chạy tới khi xong: `backoffLimit`, `activeDeadlineSeconds`, `completions`, `parallelism`
  - CronJob tạo Job theo lịch: `concurrencyPolicy: Forbid` để không chạy trùng,
    `startingDeadlineSeconds`, `timeZone` (có ở các bản mới, kiểm tra lại)
  - ⚠️ CronJob có thể không chạy hoặc (hiếm) chạy hai lần → job phải idempotent
  - Migration DB thường chạy bằng Job trước khi rollout (hoặc Helm hook)
- [ ] Graceful shutdown trong Kubernetes 🔴
  - Khi xoá pod, hai việc xảy ra **song song**: kubelet gửi SIGTERM cho container, và control
    plane gỡ pod khỏi endpoint (kube-proxy, ingress, LB cập nhật sau một lúc)
  - ⚠️ App tắt listener ngay khi nhận SIGTERM trong khi LB vẫn còn gửi request → 502/connection
    refused khi deploy
  - Cách làm: `preStop` sleep vài giây để endpoint kịp gỡ, rồi app nhận SIGTERM, ngừng nhận mới,
    làm nốt request đang chạy, đóng kết nối, exit
  - Tổng preStop + thời gian drain < `terminationGracePeriodSeconds` (mặc định 30 giây)
  - Job dài (import file, video) cần grace period dài hơn, hoặc checkpoint để làm tiếp

```yaml
spec:
  terminationGracePeriodSeconds: 45
  containers:
    - name: api
      lifecycle:
        preStop:
          exec: { command: ["sleep", "10"] }   # image distroless không có sleep: dùng preStop sleep action nếu bản K8s hỗ trợ
      readinessProbe:
        httpGet: { path: /ready, port: 8080 }
        periodSeconds: 5
      resources:
        requests: { cpu: "250m", memory: "256Mi" }
        limits: { memory: "512Mi" }
```

- [ ] Namespace, RBAC, Helm/Kustomize 🟡
  - Namespace tách môi trường/team; ResourceQuota giới hạn tài nguyên theo namespace
  - RBAC: Role/ClusterRole + RoleBinding; ServiceAccount cho pod
  - Helm: template + values, đóng gói chart; Kustomize: overlay YAML theo môi trường
  - Debug: `kubectl describe pod` (events), `kubectl logs --previous` (log của lần chạy trước khi
    crash), `kubectl get events`, `kubectl top`

### CI/CD

- [ ] Pipeline điển hình 🟢
  - Checkout → cài dependency (có cache) → lint/format check → unit test → build → integration
    test → scan bảo mật (dependency, image, secret) → push artifact → deploy staging → smoke test
    → deploy production (tự động hoặc có duyệt)
  - Nhanh là yêu cầu: pipeline 40 phút làm mọi người gộp thay đổi lớn và né chạy
  - CI (tích hợp liên tục: merge thường xuyên, luôn xanh) khác CD (continuous delivery: luôn sẵn
    sàng deploy; continuous deployment: tự deploy mỗi commit qua được pipeline)
- [ ] Artifact 🟡
  - Build một lần, promote cùng một artifact (image digest) qua staging → production. ⚠️ Build lại
    cho từng môi trường thì thứ được test không phải thứ được deploy
  - Config khác nhau theo môi trường thì đưa vào lúc deploy, không build vào image
  - Lưu artifact có version: registry image, package repository
- [ ] Cache trong CI 🟡
  - Cache dependency theo hash lockfile (`composer.lock`, `go.sum`, `package-lock.json`); cache
    layer Docker (registry cache, BuildKit)
  - ⚠️ Cache key sai → dùng dependency cũ, lỗi "chạy ở CI được mà local không" hoặc ngược lại
- [ ] Secret trong CI 🟡
  - Lưu ở secret store của CI (masked), phạm vi theo môi trường/branch
  - Tốt hơn: OIDC federation, CI xin credential tạm thời từ cloud (GitHub Actions → AWS role)
    thay vì lưu access key dài hạn
  - ⚠️ Pull request từ fork không được có secret; log in lệnh `set -x` hoặc `env` làm lộ secret;
    third-party action/plugin chạy với quyền của pipeline → pin theo commit SHA
- [ ] Quality gate 🟡
  - Điều kiện chặn merge/deploy: test xanh, coverage không giảm (hoặc ngưỡng), không lỗi lint,
    không CVE nghiêm trọng, review được duyệt, migration được review
  - ⚠️ Gate quá chặt nhưng flaky → mọi người học cách bỏ qua. Test flaky phải được sửa hoặc cách
    ly. Chi tiết: [20-testing-quality.md](20-testing-quality.md)

### Deploy

- [ ] Các chiến lược 🟢

| Chiến lược | Cách làm | Rollback | Ưu | Nhược |
|---|---|---|---|---|
| Recreate | tắt hết bản cũ, bật bản mới | deploy lại bản cũ | đơn giản, không chạy song song hai bản | downtime |
| Rolling | thay dần từng nhóm | rollout ngược, mất thời gian | không cần gấp đôi hạ tầng | hai bản chạy song song; lỗi ảnh hưởng dần tới mọi người |
| Blue-green | dựng đủ môi trường mới, chuyển traffic một lần | chuyển traffic về môi trường cũ, gần như tức thì | rollback nhanh, test được trước khi chuyển | tốn gấp đôi tài nguyên lúc deploy; DB dùng chung vẫn phải tương thích |
| Canary | cho một phần nhỏ traffic (1%, 5%, 25%...) vào bản mới, theo dõi metric | dồn traffic về bản cũ | giới hạn phạm vi ảnh hưởng, dựa vào dữ liệu thật | cần metric tốt và tự động hoá (Argo Rollouts, Flagger) |

  - ⚠️ Canary chỉ có ích khi có tiêu chí dừng rõ: tỉ lệ lỗi, latency so với bản cũ. Canary 1%
    với traffic thấp không đủ dữ liệu để kết luận
- [ ] Feature flag 🟢
  - Deploy code ở trạng thái tắt, bật dần theo user/nhóm/phần trăm. Tách deploy (kỹ thuật) khỏi
    release (quyết định sản phẩm); tắt nhanh khi lỗi mà không cần deploy
  - ⚠️ Flag là nợ kỹ thuật: dọn flag cũ; tổ hợp nhiều flag khó test; flag phụ thuộc service ngoài
    phải có giá trị mặc định khi service đó lỗi
  - Các loại: release flag (ngắn hạn), ops flag/kill switch (lâu dài), experiment flag (A/B)
- [ ] Rollback 🟡
  - Rollback code dễ; rollback **data** khó. Migration đã xoá cột, job đã gửi email, message đã
    publish theo format mới thì không quay lại được
  - Luôn có kế hoạch rollback trước khi deploy; đôi khi roll forward (sửa nhanh) an toàn hơn
  - Config thay đổi cũng là deploy: có version, review, rollback được
- [ ] Database migration khi deploy: expand/contract 🔴
  - Vấn đề: trong rolling/blue-green, bản cũ và bản mới cùng chạy trên một DB. Migration không
    tương thích ngược làm bản cũ lỗi ngay khi migration chạy
  - Expand/contract (parallel change), ví dụ đổi tên cột `name` → `full_name`:
    1. **Expand**: thêm cột `full_name` (nullable). Deploy code ghi cả hai cột, đọc cột cũ
    2. **Migrate data**: backfill theo batch nhỏ, không khoá bảng lâu
    3. Deploy code đọc cột mới (vẫn ghi cả hai để có thể rollback)
    4. Deploy code chỉ dùng cột mới
    5. **Contract**: xoá cột cũ ở một lần deploy sau, khi chắc chắn không rollback nữa
  - ⚠️ Thêm cột `NOT NULL` không default, thêm index trên bảng lớn, đổi kiểu cột có thể khoá bảng
    hoặc rewrite bảng → dùng thao tác online (`CREATE INDEX CONCURRENTLY` ở PostgreSQL, online DDL
    của MySQL, gh-ost/pt-online-schema-change). Chi tiết: [03-database-sql.md](03-database-sql.md)
  - ⚠️ Chạy migration từ mỗi pod lúc khởi động → nhiều pod chạy cùng lúc. Chạy một lần, tách
    bước (Job, bước riêng trong pipeline), có lock
  - Thứ tự: migration tương thích ngược chạy **trước** code mới; bước contract chạy **sau** khi code
    cũ không còn
- [ ] Zero-downtime deploy 🟡
  - Cần đủ: nhiều replica, readiness probe đúng, graceful shutdown (xem phần Kubernetes), draining
    ở LB, migration tương thích ngược, API/message tương thích ngược, session không nằm trong
    process, cache warm-up nếu cần
  - PHP truyền thống: đổi symlink `current` + reload PHP-FPM (reset OPcache). ⚠️ OPcache với
    `validate_timestamps=0` và symlink → phải reload FPM hoặc dùng `realpath` root trong Nginx

### IaC và GitOps

- [ ] Terraform 🟡
  - Khai báo trạng thái mong muốn bằng HCL; provider nói chuyện với API của cloud
  - `terraform plan`: so trạng thái mong muốn với state và thực tế, in ra thay đổi. `apply`: thực
    hiện. ⚠️ Đọc plan kỹ: dòng `must be replaced` (destroy rồi create) với DB là mất dữ liệu
  - State: file ánh xạ resource trong code ↔ resource thật. Lưu remote (S3, GCS, Terraform Cloud),
    có locking để hai người không apply cùng lúc (S3 + DynamoDB lock truyền thống; bản mới có lock
    bằng S3 trực tiếp, kiểm tra lại theo phiên bản)
  - ⚠️ State chứa secret dạng plaintext → mã hoá, giới hạn quyền truy cập
  - Drift: ai đó sửa tay trên console → thực tế khác code. Phát hiện bằng `plan` định kỳ; sửa bằng
    cách đưa thay đổi vào code hoặc apply đè
  - Module để tái dùng; tách state theo môi trường/phạm vi để giảm blast radius; `import` đưa
    resource có sẵn vào quản lý; `prevent_destroy` cho resource quan trọng
- [ ] Ansible đại ý 🟡
  - Quản lý cấu hình máy (cài package, sửa file config, restart service) qua SSH, không cần agent.
    Playbook YAML, module idempotent
  - Khác Terraform: Terraform dựng hạ tầng (tạo máy, mạng), Ansible cấu hình bên trong máy.
    Với container/immutable infrastructure, nhu cầu Ansible giảm
- [ ] GitOps, Argo CD 🔴
  - Git là nguồn sự thật cho trạng thái cluster. Agent trong cluster (Argo CD, Flux) liên tục kéo
    manifest từ Git và đồng bộ; lệch thì báo hoặc tự sửa
  - Mô hình pull: CI không cần credential vào cluster; mọi thay đổi có review và lịch sử; rollback
    = revert commit
  - Hay tách repo code và repo manifest; CI build image rồi cập nhật tag trong repo manifest
  - ⚠️ Sửa tay bằng `kubectl` sẽ bị ghi đè khi sync; secret không để plaintext trong Git (Sealed
    Secrets, SOPS, External Secrets)

### Cloud (AWS làm ví dụ)

- [ ] Bảng dịch vụ và tương đương 🟡

| Nhu cầu | AWS | GCP | Azure |
|---|---|---|---|
| VM | EC2 | Compute Engine | Virtual Machines |
| Container được quản lý | ECS (Fargate), EKS | Cloud Run, GKE | Container Apps, AKS |
| Function | Lambda | Cloud Run functions | Azure Functions |
| Object storage | S3 | Cloud Storage | Blob Storage |
| DB quan hệ | RDS, Aurora | Cloud SQL, AlloyDB | Azure SQL, Azure Database for PostgreSQL/MySQL |
| Key-value/document | DynamoDB | Firestore, Bigtable | Cosmos DB |
| Redis/Memcached | ElastiCache | Memorystore | Azure Cache for Redis |
| Queue / pub-sub | SQS / SNS | Pub/Sub | Service Bus, Event Grid |
| CDN | CloudFront | Cloud CDN | Front Door |
| DNS | Route 53 | Cloud DNS | Azure DNS |
| Danh tính, quyền | IAM | IAM | Entra ID + RBAC |
| Mạng riêng | VPC | VPC | VNet |
| Log, metric | CloudWatch | Cloud Logging/Monitoring | Azure Monitor |

- [ ] Region và AZ 🟡
  - Region: vùng địa lý; AZ: các trung tâm dữ liệu độc lập trong region. Chạy app ở ít nhất 2 AZ
    để chịu được một AZ sự cố
  - ⚠️ Truyền dữ liệu giữa AZ có tính phí; đặt tất cả vào một AZ để tiết kiệm là đánh đổi HA
- [ ] Compute 🟡
  - EC2: tự quản OS, linh hoạt nhất. Loại burstable (`t3`, `t4g`) dùng CPU credit: hết credit là
    chậm hẳn. Spot rẻ nhưng bị thu hồi với thông báo ngắn → hợp worker stateless, batch
  - ECS: orchestrator của AWS, đơn giản hơn Kubernetes; Fargate: không quản node. EKS: Kubernetes
    được quản lý control plane
  - Lambda: chạy function theo sự kiện (API Gateway, SQS, S3, lịch), tính tiền theo thời gian chạy
- [ ] Serverless trade-off 🔴
  - Ưu: không quản server, scale về 0, trả tiền theo dùng, tích hợp sự kiện sẵn
  - Cold start: instance mới phải khởi tạo runtime và code → request đầu chậm; nặng hơn với JVM,
    package lớn, chạy trong VPC (đã cải thiện nhiều). Giảm bằng provisioned concurrency,
    SnapStart (Java), code khởi động nhẹ
  - Giới hạn: Lambda chạy tối đa 15 phút; giới hạn payload, bộ nhớ, `/tmp`; API Gateway có timeout
    riêng ngắn hơn nhiều (kiểm tra lại giới hạn hiện tại)
  - ⚠️ Concurrency: mỗi instance xử lý một request tại một thời điểm → spike tạo hàng nghìn
    instance, mỗi cái mở kết nối DB → cạn connection. Dùng RDS Proxy, hoặc giới hạn reserved
    concurrency. Giới hạn concurrency của tài khoản theo region (kiểm tra lại quota)
  - ⚠️ Chi phí: rẻ với tải thấp/không đều; tải cao và đều thì container/VM thường rẻ hơn
  - Khó chạy local, khó debug, vendor lock-in; state phải nằm ngoài
- [ ] Storage và DB 🟡
  - S3: object storage, bền vững rất cao, strong read-after-write consistency (từ 12/2020).
    Storage class (Standard, IA, Glacier) và lifecycle rule để giảm chi phí; presigned URL cho
    client upload/download trực tiếp; versioning chống xoá nhầm
    - ⚠️ Bucket public nhầm là nguồn rò rỉ dữ liệu kinh điển → bật Block Public Access, phục vụ
      qua CloudFront với origin access control
  - RDS: DB quan hệ được quản lý (backup, patch, failover). Multi-AZ = standby đồng bộ để
    failover (không đọc được ở chế độ cổ điển); read replica = bản sao bất đồng bộ để đọc (có
    replication lag). Hai thứ khác mục đích
  - Aurora: storage phân tán tách khỏi compute, replica chia sẻ storage nên lag thấp và failover
    nhanh; đắt hơn RDS thường. ⚠️ Failover đổi endpoint → app phải reconnect (DNS cache, pool)
  - DynamoDB: key-value/document, scale ngang, latency ổn định; thiết kế theo access pattern
    (partition key, sort key, GSI). ⚠️ Hot partition; query không đi theo key là scan đắt. Chi tiết:
    [04-nosql-search-storage.md](04-nosql-search-storage.md)
  - ElastiCache: Redis/Valkey/Memcached được quản lý. Chi tiết: [11-cache.md](11-cache.md)
- [ ] SQS và SNS 🟡
  - SQS: queue pull-based. Standard: at-least-once, thứ tự không đảm bảo, throughput rất cao.
    FIFO: đúng thứ tự trong message group, có deduplication, throughput giới hạn hơn
  - Visibility timeout: message đang được xử lý bị ẩn; không xoá kịp thì hiện lại và bị xử lý lần
    nữa → consumer phải idempotent, visibility timeout > thời gian xử lý
  - Dead-letter queue sau N lần nhận thất bại; long polling giảm request rỗng
  - SNS: pub/sub push tới nhiều subscriber. Fan-out: SNS topic → nhiều SQS queue, mỗi service một
    queue riêng. EventBridge: event bus có rule lọc. Chi tiết: [12-messaging.md](12-messaging.md)
- [ ] CloudFront và Route 53 🟡
  - CloudFront: CDN, cache theo cache policy, origin là S3/ALB; chạy được logic nhỏ ở edge
  - Route 53: DNS với routing policy (simple, weighted, latency, failover, geolocation), health
    check, alias record cho apex domain trỏ tới ALB/CloudFront
- [ ] IAM 🟡
  - Principal (user, role, service), policy (JSON: `Effect`, `Action`, `Resource`, `Condition`);
    deny tường minh thắng allow
  - User: danh tính lâu dài với credential dài hạn (access key). Role: được "assume" để lấy
    credential tạm thời qua STS, tự hết hạn
  - Quy tắc: người dùng đăng nhập qua SSO; app chạy trên EC2/ECS/Lambda/EKS dùng role
    (instance profile, task role, IRSA/EKS Pod Identity), không nhét access key vào code/env
  - Least privilege: chỉ cấp action và resource cần; bắt đầu hẹp rồi mở dần; review định kỳ
  - ⚠️ `"Action": "*"`, `"Resource": "*"` cho tiện; access key dài hạn bị commit lên Git (bot quét
    được trong vài phút); tài khoản root dùng hằng ngày, không MFA
  - Tách tài khoản AWS theo môi trường (AWS Organizations) để giảm blast radius
- [ ] VPC và CloudWatch 🟡
  - VPC, subnet, security group, NAT gateway, VPC endpoint: xem [02-networking.md](02-networking.md)
  - CloudWatch: metric, log, alarm, dashboard. ⚠️ Log không đặt retention là lưu vĩnh viễn và tính
    tiền mãi; metric tuỳ chỉnh với cardinality cao cũng tốn

### Môi trường, config, chi phí

- [ ] dev, staging, production 🟢
  - Staging càng giống production càng bắt được lỗi: cùng image, cùng kiểu hạ tầng, cùng phiên bản
    DB, cấu hình khác ở giá trị chứ không ở cấu trúc
  - ⚠️ Staging khác production (dữ liệu nhỏ, không có CDN, không có tải, cấu hình tay) thì bug về
    hiệu năng, migration trên bảng lớn, timeout vẫn lọt
  - ⚠️ Copy dữ liệu production về staging phải ẩn danh dữ liệu cá nhân; staging không được gửi
    email/SMS/thanh toán thật
- [ ] 12-factor app 🟡
  - Các ý hay được hỏi: một codebase nhiều deploy; khai báo dependency tường minh; **config qua môi
    trường**, không trong code; backing service (DB, queue) là tài nguyên gắn vào qua URL; tách
    build, release, run; process **stateless**, dữ liệu ở backing service; bind port; scale bằng
    process; **disposability** (khởi động nhanh, tắt êm); dev/prod parity; **log ra stdout** như
    event stream; admin task (migration) chạy như process một lần
  - Ra đời thời Heroku nhưng vẫn là nền của container/Kubernetes
- [ ] Quản lý config và secret 🟡
  - Config không bí mật: env var, ConfigMap, file config theo môi trường
  - Secret: secret manager (AWS Secrets Manager, SSM Parameter Store, Vault, GCP Secret Manager),
    đưa vào lúc chạy; xoay vòng (rotation) định kỳ; audit ai đọc
  - Validate config khi khởi động, thiếu thì fail ngay thay vì lỗi lúc chạy
  - ⚠️ `.env` bị commit; secret in ra log lúc khởi động; cùng một secret dùng cho mọi môi trường
  - Chi tiết về secret: [10-security.md](10-security.md)
- [ ] Cost awareness 🔴
  - Nguồn tiền hay bị bỏ qua: data transfer ra Internet và giữa AZ/region, NAT gateway theo GB,
    log/metric (lưu lâu, cardinality cao), snapshot/volume mồ côi, LB không dùng, môi trường dev
    chạy 24/7, instance chọn quá cỡ
  - Công cụ: tagging theo team/service để phân bổ chi phí, budget alert, Cost Explorer; rightsizing
    theo metric sử dụng thật
  - Mô hình giá: on-demand, reserved/savings plan (cam kết dài hạn đổi giảm giá), spot (rẻ, bị thu
    hồi); ARM (Graviton) thường rẻ hơn cho cùng hiệu năng (kiểm tra lại với workload của bạn)
  - Góc senior: đưa chi phí vào quyết định thiết kế (ví dụ ước lượng chi phí cho mỗi 1 triệu
    request), biết trade-off chi phí và HA, không tối ưu sớm những khoản nhỏ

## Senior trả lời khác gì

**"Làm sao deploy mà người dùng không bị gián đoạn?"**
- Mid: dùng rolling update hoặc blue-green.
- Senior: chiến lược deploy chỉ là một phần. Nói cả chuỗi: readiness probe đúng, graceful shutdown
  và preStop để khớp với việc gỡ endpoint, draining ở LB, migration expand/contract, API và message
  tương thích ngược vì hai bản chạy song song, và kế hoạch rollback kể cả phần dữ liệu.

**"Liveness probe nên kiểm tra gì?"**
- Mid: gọi `/health`, kiểm tra DB và Redis kết nối được.
- Senior: liveness chỉ trả lời "process có kẹt không"; kiểm tra dependency ở liveness biến sự cố DB
  thành restart hàng loạt. Readiness cũng phải cân nhắc dependency dùng chung. Có startup probe cho
  app khởi động chậm, timeout probe tính đến GC và throttle.

**"Có nên dùng Kubernetes không?"**
- Mid: có, vì là chuẩn, scale tốt.
- Senior: tuỳ quy mô team và số service. Kubernetes cho khả năng chuẩn hoá và tự động hoá lớn, nhưng
  cần người vận hành (nâng cấp, network, bảo mật). Vài service với team nhỏ thì ECS/Cloud Run/PaaS
  thường đủ và rẻ công hơn. Nói được khi nào chuyển.

**"Lambda hay container?"**
- Mid: Lambda rẻ hơn vì không phải trả tiền khi không chạy.
- Senior: rẻ với tải thấp hoặc không đều; tải cao ổn định thì container rẻ hơn. Xét cold start với
  yêu cầu latency, giới hạn 15 phút, concurrency làm cạn connection DB, khả năng debug và lock-in.

**"Đổi tên một cột đang dùng trên production."**
- Mid: viết migration `RENAME COLUMN` rồi deploy.
- Senior: rename làm bản code cũ đang chạy song song lỗi ngay. Dùng expand/contract nhiều lần
  deploy, backfill theo batch, chỉ xoá cột cũ khi không còn khả năng rollback; kiểm tra thao tác nào
  khoá bảng trên DB đang dùng.

## Tình huống

1. **Mỗi lần DB chậm vài giây, toàn bộ pod API restart cùng lúc và hệ thống sập vài phút.**
   - Gợi ý:
     - Liveness probe đang kiểm tra DB → bỏ dependency khỏi liveness
     - Xem lại readiness, timeout của probe
     - Thêm circuit breaker/timeout cho DB để app vẫn trả lỗi nhanh thay vì treo

2. **Pod trạng thái `CrashLoopBackOff` sau khi deploy bản mới.**
   - Gợi ý:
     - `kubectl describe pod` (events, exit code, `OOMKilled`), `kubectl logs --previous`
     - Hay gặp: thiếu config/secret, không kết nối được dependency, liveness giết app khởi động
       chậm, memory limit thấp
     - Rollback trước (`kubectl rollout undo`), điều tra sau

3. **Terraform plan báo sẽ replace instance RDS production chỉ vì đổi một tham số nhỏ.**
   - Gợi ý:
     - Không apply; tìm thuộc tính nào bắt buộc replace (tên, engine, một số tham số)
     - Xem có cách đổi tại chỗ không, hoặc lên kế hoạch migration có backup
     - Bảo vệ về sau: `prevent_destroy`, deletion protection của RDS, review plan bắt buộc

4. **Hoá đơn AWS tháng này tăng 40% mà traffic không đổi.**
   - Gợi ý:
     - Cost Explorer theo service và tag: thường là data transfer, NAT gateway, log, resource quên xoá
     - Ví dụ: app ở private subnet tải file lớn từ S3 qua NAT gateway → thêm VPC endpoint
     - Đặt budget alert, tag bắt buộc

5. **Cần thêm cột `NOT NULL` vào bảng `orders` 200 triệu dòng mà không downtime.**
   - Gợi ý:
     - Expand: thêm cột nullable (hoặc có default nếu DB hỗ trợ thêm mà không rewrite bảng)
     - Code mới ghi cột; backfill theo batch có nghỉ giữa các batch, theo dõi replication lag
     - Thêm ràng buộc sau khi backfill xong, dùng cách validate không khoá lâu của DB đang dùng

6. **Secret AWS access key bị lộ trên GitHub public repo.**
   - Gợi ý:
     - Vô hiệu hoá/xoay key ngay, trước khi xoá commit (lịch sử và bot đã có bản sao)
     - Kiểm tra CloudTrail xem key đã bị dùng làm gì (thường là tạo máy đào coin)
     - Phòng ngừa: role thay access key, OIDC cho CI, secret scanning trước commit

## ❓ Câu hỏi hay gặp

🟢
- Container khác VM thế nào?
- Viết Dockerfile tốt cần lưu ý gì?
- Rolling, blue-green, canary khác nhau thế nào? Rollback mỗi loại ra sao?
- Feature flag giải quyết vấn đề gì?
- Vì sao không lưu dữ liệu trong container?

🟡
- `ENTRYPOINT` và `CMD` khác nhau thế nào? Shell form có vấn đề gì?
- Liveness, readiness, startup probe khác nhau thế nào?
- Request và limit trong Kubernetes khác nhau thế nào? Vượt memory limit và vượt CPU limit thì sao?
- Làm sao deploy mà người dùng không bị gián đoạn?
- Secret trong Kubernetes có an toàn không?
- IAM role khác IAM user thế nào? Least privilege là gì?
- Terraform state là gì? Drift là gì?
- 12-factor app gồm những ý gì quan trọng nhất?

🔴
- Làm migration DB tương thích ngược khi deploy thế nào?
- Vì sao pod đã bắt được SIGTERM mà vẫn có request lỗi lúc deploy?
- PodDisruptionBudget dùng để làm gì? Nó không bảo vệ khỏi cái gì?
- Serverless có những trade-off gì? Khi nào không nên dùng?
- GitOps khác mô hình CI push deploy thế nào?
- Bạn kiểm soát chi phí cloud thế nào?

## Bài tập tự làm

1. Viết Dockerfile multi-stage cho một app trong repo này (Go hoặc PHP): chạy non-root, có
   `.dockerignore`, exec form. So sánh kích thước image trước và sau khi tối ưu, giải thích từng
   thay đổi.
2. Viết manifest Kubernetes (Deployment, Service, Ingress, HPA, PDB) cho một API stateless với
   probes, resource, preStop. Ghi chú bên cạnh mỗi giá trị vì sao chọn con số đó.
3. Viết kế hoạch expand/contract từng bước (mỗi bước ghi migration và thay đổi code) để tách cột
   `address` dạng text thành bảng `addresses` riêng, trong khi hệ thống vẫn chạy.
4. Thiết kế pipeline CI/CD (dạng YAML giả hoặc sơ đồ) cho một monorepo hai service: cache, test,
   build image một lần, scan, deploy staging, canary production, điều kiện dừng canary, rollback.
5. Ước lượng chi phí hàng tháng trên AWS cho một app: 2 AZ, 3 container, RDS PostgreSQL Multi-AZ,
   Redis, ALB, NAT gateway, 500 GB traffic ra Internet. Ghi rõ giả định và khoản nào lớn nhất.

> Nộp bài vào đây để được review.
