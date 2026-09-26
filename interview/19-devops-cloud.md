# 19. DevOps và Cloud

> [← Mục lục](README.md) · Trọng tâm: **Docker, Kubernetes, CI/CD, deploy không downtime, IaC, AWS** cho ứng dụng PHP-FPM/Laravel; đối chiếu Go/Java khi có ích.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn.

File gồm hai phần:

1. **Lộ trình kiến thức** (phần chính): ba chặng từ nền tới senior. Mỗi module có:
   - **Vì sao cần học**: module này dùng vào việc gì và hay bị hỏi thế nào.
   - **Học gì**: các khái niệm, giải thích bằng lời thường kèm ví dụ, và các cạm bẫy ⚠️. Đọc phần
     này để biết cần học gì, rồi học sâu qua tài liệu ở mục Đọc.
   - **Đọc**: tài liệu gốc.
   - **Nắm chắc khi**: tiêu chí tự kiểm tra. Chỉ tick ô khi làm được điều đó mà không cần nhìn
     tài liệu.
2. **Câu hỏi thường gặp** (bonus): mỗi câu kèm hướng trả lời mong đợi, gồm ý phải có, điểm
   cộng senior và red flag. Dùng để kiểm tra sau khi học, không dùng để học thuộc.

Observability và xử lý sự cố nằm ở [18-reliability-observability.md](18-reliability-observability.md).
Linux nền (signal, PID 1, cgroup, namespace) ở [01-os-linux.md](01-os-linux.md).

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Docker docs: Building best practices](https://docs.docker.com/build/building/best-practices/) | Official docs | Dockerfile, layer, multi-stage, cache. Đọc hết trang này trước |
| [Kubernetes docs: Concepts](https://kubernetes.io/docs/concepts/workloads/pods/) | Official docs | Nguồn chuẩn cho mọi hành vi của Kubernetes. Mục *Workloads*, *Services*, *Configuration*, *Security* |
| *Kubernetes in Action* (Marko Lukša, Manning) | Sách | Hiểu Kubernetes từ gốc, có hình vẽ luồng pod, service, rollout |
| [learnk8s.io](https://learnk8s.io/production-best-practices) | Blog kỹ thuật | Checklist production, bài graceful shutdown rất chi tiết |
| [Terraform docs](https://developer.hashicorp.com/terraform/language/state) | Official docs | State, backend, module, locking |
| [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) | Whitepaper | Sáu trụ cột: vận hành, bảo mật, độ tin cậy, hiệu năng, chi phí, bền vững |
| [The Twelve-Factor App](https://12factor.net/) | Bài viết kinh điển | Nguyên tắc app chạy tốt trên container/PaaS. Đọc hết, khoảng 1 giờ |
| [Laravel docs: Deployment](https://laravel.com/docs/deployment), [Queues](https://laravel.com/docs/queues), [Octane](https://laravel.com/docs/octane) | Official docs | Tối ưu khi deploy, worker, runtime chạy lâu |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Viết Dockerfile đúng, hiểu pipeline, các chiến lược deploy, 12-factor | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.9 | Chạy app PHP trên Kubernetes đúng cách: probe, resource, graceful shutdown, secret, CI an toàn, Terraform | 10–12 ngày |
| **3. Senior** 🔴 | 3.1–3.7 | Bảo mật cluster, migration không downtime, GitOps, supply chain, chọn dịch vụ cloud, serverless, chi phí | 10–12 ngày |

Học theo thứ tự: chặng 2 cần hiểu signal và PID 1 từ module 1.2 để làm graceful shutdown, chặng
3 cần rolling update của chặng 2 để hiểu vì sao migration phải expand/contract. Nên dựng một
cluster local (kind, minikube hoặc k3d) và làm tay mọi thứ trong chặng 2.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Container và Docker cơ bản

**Vì sao cần học:** Hầu hết hệ thống PHP hiện nay chạy trong container, từ docker compose ở máy
dev tới Kubernetes trên production. Hiểu layer và build cache quyết định một lần build mất 30 giây
hay 10 phút. Hay bị hỏi: container khác VM thế nào, viết Dockerfile tốt cần lưu ý gì.

**Học gì**

*Image và container*
- *Image* là một template chỉ đọc, gồm nhiều *layer* xếp chồng lên nhau. Mỗi layer là tập file thay
  đổi so với layer bên dưới.
- *Container* là một process chạy từ image, có thêm một layer ghi được ở trên cùng. Layer này mất
  khi xoá container.
- Quan hệ giống class và object: một image chạy được thành nhiều container.

*Container không phải VM*

| | Container | VM |
|---|---|---|
| Kernel | Dùng chung kernel với host | Kernel riêng, chạy trên hypervisor |
| Cô lập bằng | Namespace và cgroup | Hypervisor |
| Khởi động | Nhanh | Chậm hơn |
| Độ nặng | Nhẹ | Nặng hơn |
| Độ cô lập | Yếu hơn: lỗ hổng kernel ảnh hưởng mọi container | Mạnh hơn |

- *Namespace* là tính năng của Linux cho mỗi nhóm process một "góc nhìn" riêng về PID, network,
  mount, user.
  - Ví dụ: trong container, app thấy mình là PID 1 và chỉ thấy các process của container.
- *cgroup* giới hạn tài nguyên (CPU, RAM) của một nhóm process.
- Chi tiết namespace và cgroup ở [01-os-linux.md](01-os-linux.md).
- *MicroVM* (Firecracker, dùng bởi Lambda/Fargate) là điểm giữa: VM rất nhẹ, có kernel riêng, khởi
  động nhanh gần như container.
- ⚠️ Trên macOS/Windows, container Linux chạy trong một VM Linux ẩn. *Bind mount* (gắn thư mục của
  máy thật vào container) phải đi qua lớp VM này, nên hiệu năng khác hẳn production.
  - Ví dụ: Laravel trên Mac với source bind mount thường chậm hơn nhiều so với trên server Linux.

*Layer và build cache*
- Mỗi lệnh `RUN`, `COPY`, `ADD` tạo một layer.
- Docker cache từng layer. Layer nào đổi thì mọi layer sau nó phải build lại.
- Vì vậy đặt thứ ít đổi lên trước:

  ```dockerfile
  COPY composer.json composer.lock ./
  RUN composer install --no-dev --no-scripts   # chỉ chạy lại khi lockfile đổi
  COPY . .                                     # code đổi thường xuyên, đặt sau cùng
  ```
- ⚠️ Xoá file ở layer sau không làm image nhỏ đi, vì layer trước vẫn chứa file đó. Cài và dọn phải
  nằm trong cùng một `RUN`:

  ```dockerfile
  RUN apt-get update && apt-get install -y libzip-dev && rm -rf /var/lib/apt/lists/*
  ```

*Multi-stage và image base*
- *Multi-stage build*: một Dockerfile có nhiều `FROM`.
  - Stage build có compiler, dev dependency.
  - Stage cuối chỉ copy những thứ cần để chạy. Image production nhỏ hơn và ít lỗ hổng hơn.
- Các loại image base:

  | Image base | Là gì |
  |---|---|
  | `distroless` | Chỉ có runtime, không shell, không package manager |
  | `alpine` | Rất nhỏ, dùng thư viện C musl |
  | `-slim` | Debian rút gọn, dùng glibc |
  | `scratch` | Rỗng hoàn toàn, hợp với Go binary tĩnh |

- ⚠️ Alpine dùng musl thay cho glibc, nên khác ở DNS resolver, hiệu năng và extension native. Đôi
  khi `-slim` (Debian) ít rắc rối hơn.

*Dữ liệu và mạng*
- ⚠️ Container là tạm thời. Dữ liệu phải ở volume hoặc dịch vụ ngoài (DB, S3), không ở filesystem
  của container.
- Volume có hai loại chính:
  - Named volume: Docker tự quản lý nơi lưu.
  - Bind mount: một thư mục cụ thể của host.
- Network của compose: các service gọi nhau bằng tên service.
  - Ví dụ: app Laravel đặt `DB_HOST=mysql` nếu service DB tên là `mysql`.

**Đọc**
- Docker: [Building best practices](https://docs.docker.com/build/building/best-practices/), [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/), [Build cache](https://docs.docker.com/build/cache/)
- [distroless](https://github.com/GoogleContainerTools/distroless): README, phần chọn image
- Linux nền: [01-os-linux.md](01-os-linux.md) (namespace, cgroup)

**Nắm chắc khi**
- [ ] Giải thích được vì sao đổi một dòng code PHP mà `composer install` không chạy lại
- [ ] Viết được Dockerfile multi-stage và so kích thước trước/sau (bài tập 1)
- [ ] Nói được 3 khác biệt thực tế giữa container và VM, kể cả về bảo mật

#### 1.2 Dockerfile an toàn và chạy đúng

**Vì sao cần học:** Dockerfile sai thường không làm app lỗi ngay, mà gây hậu quả âm thầm: secret
nằm vĩnh viễn trong image, hoặc mỗi lần deploy cắt ngang request vì app không nhận được tín hiệu
tắt. Hay bị hỏi: shell form khác exec form thế nào, vì sao `docker stop` mất đúng 10 giây.

**Học gì**

*Không chạy bằng root*
- Mặc định container chạy bằng root (UID 0).
  - Nếu không bật *user namespace* (ánh xạ UID trong container sang một UID khác ngoài host) thì đó
    cũng chính là UID root của host. Kẻ tấn công thoát được khỏi container là có quyền root trên
    host.
- Cách làm: dùng `USER` để chạy bằng user không phải root. Để filesystem chỉ đọc nếu được.
- ⚠️ Non-root có bind được port < 1024 hay không tuỳ runtime và sysctl
  `net.ipv4.ip_unprivileged_port_start`. Quen listen 8080 để không phụ thuộc vào điều đó.

*Secret và .dockerignore*
- `.dockerignore` loại file khỏi *build context* (thư mục được gửi cho Docker lúc build). Nên loại
  `.git`, `vendor`, `node_modules`, `.env`, log. Lợi ích:
  - Build context nhỏ, build nhanh hơn.
  - Tránh vô hiệu cache: file log đổi không làm `COPY . .` phải build lại.
  - Tránh lộ secret.
- ⚠️ Các đường lộ secret:
  - `COPY . .` kèm `.env` → secret nằm trong image mãi mãi.
  - `ARG`/`ENV` chứa secret → lộ qua `docker history` hoặc `docker inspect`.
- Cách đúng: `RUN --mount=type=secret` (BuildKit). Secret chỉ được gắn trong lúc chạy lệnh đó, không
  ghi vào layer.
- `RUN --mount=type=cache` giữ cache của package manager (composer, apt) giữa các lần build.

*ENTRYPOINT, CMD và PID 1*
- `ENTRYPOINT` là chương trình chính, `CMD` là đối số mặc định.
  - `docker run image args` thay `CMD` bằng `args`, giữ nguyên `ENTRYPOINT`.
- *PID 1* là process đầu tiên trong container. Khi `docker stop` hoặc Kubernetes xoá pod:
  1. SIGTERM (tín hiệu "hãy tắt đi") được gửi tới PID 1.
  2. Hết *grace period* (thời gian chờ, mặc định 10 giây với `docker stop`) mà process chưa thoát
     thì bị SIGKILL, tức giết ngay.

| | Exec form `CMD ["php-fpm"]` | Shell form `CMD php-fpm` |
|---|---|---|
| PID 1 là | `php-fpm` | `/bin/sh -c` |
| SIGTERM | Tới app | ⚠️ Shell không chuyển tiếp, app không nhận được |
| Khi stop | App tắt ngay | Chờ hết grace period rồi bị SIGKILL |

- Entrypoint script phải kết thúc bằng `exec "$@"`. `exec` thay process shell bằng app, nên app trở
  thành PID 1.

  ```sh
  #!/bin/sh
  set -e
  php artisan config:cache   # các bước chuẩn bị
  exec "$@"                  # app thay chỗ shell, thành PID 1
  ```

*HEALTHCHECK và depends_on*
- `HEALTHCHECK` trong Dockerfile được Docker và Compose dùng.
  - Ví dụ: `depends_on: condition: service_healthy` chờ DB healthy rồi mới bật app.
- ⚠️ Kubernetes bỏ qua `HEALTHCHECK`, nó dùng probe (module 2.4).
- ⚠️ `depends_on` không có condition chỉ đảm bảo thứ tự khởi động, không đảm bảo service kia đã sẵn
  sàng.
  - Ví dụ: container MySQL đã start nhưng chưa nhận kết nối, app chạy migrate và lỗi.

**Đọc**
- Docker: [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) (mục [shell and exec form](https://docs.docker.com/reference/dockerfile/#shell-and-exec-form), [ENTRYPOINT](https://docs.docker.com/reference/dockerfile/#entrypoint), [HEALTHCHECK](https://docs.docker.com/reference/dockerfile/#healthcheck), [USER](https://docs.docker.com/reference/dockerfile/#user)), [Build secrets](https://docs.docker.com/build/building/secrets/), [Control startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- Docker: [Engine security](https://docs.docker.com/engine/security/)

**Nắm chắc khi**
- [ ] Chứng minh được bằng `docker stop` và đo thời gian: shell form bị kill sau 10 giây, exec form tắt ngay
- [ ] Tìm được secret trong một image bằng `docker history` hoặc giải nén layer
- [ ] Viết được entrypoint script chạy vài bước chuẩn bị rồi chuyển PID 1 cho app

#### 1.3 CI/CD và chiến lược deploy

**Vì sao cần học:** Pipeline quyết định team deploy được mấy lần một ngày, và mỗi lần deploy có
đáng sợ không. Hay bị hỏi: so sánh rolling, blue-green, canary và cách rollback của từng loại,
cùng tiêu chí để dừng một canary.

**Học gì**

*Pipeline*
- Các bước điển hình:
  1. Checkout code.
  2. Cài dependency (có cache).
  3. Lint.
  4. Unit test.
  5. Build.
  6. Integration test.
  7. Scan dependency, image, secret.
  8. Push artifact.
  9. Deploy staging.
  10. Smoke test (kiểm tra nhanh vài luồng chính).
  11. Deploy production.
- Nhanh là yêu cầu. Pipeline 40 phút làm mọi người gộp nhiều thay đổi thành một lần lớn, và tìm
  cách né chạy.

*CI và CD*
- *CI* (continuous integration): merge vào nhánh chính thường xuyên, nhánh chính luôn xanh.
- *CD* có hai nghĩa:
  - Continuous delivery: code luôn ở trạng thái sẵn sàng deploy, bấm nút là đi.
  - Continuous deployment: mỗi commit qua được pipeline thì tự deploy.

*Build một lần, promote nhiều nơi*
- Build image một lần, rồi promote cùng một artifact qua staging, production. Artifact được định
  danh bằng *image digest*, mã hash dạng `sha256:...` của image.
- ⚠️ Build lại cho từng môi trường thì thứ được test không phải thứ được deploy. Dependency có thể đã
  đổi giữa hai lần build.

*Chiến lược deploy*

| | Cách làm | Downtime | Rollback | Lưu ý |
|---|---|---|---|---|
| Recreate | Tắt hết bản cũ rồi bật bản mới | Có | Deploy lại bản cũ | Đơn giản nhất |
| Rolling | Thay dần từng phần | Không | Mất thời gian, cũng phải thay dần | Hai bản chạy song song |
| Blue-green | Dựng đủ môi trường mới, chuyển traffic một lần | Không | Gần tức thì, chuyển traffic về | Tốn gấp đôi lúc deploy. DB dùng chung vẫn phải tương thích cả hai bản |
| Canary | Cho 1%, 5%, 25% traffic vào bản mới, so metric với bản cũ | Không | Nhanh, rút traffic khỏi canary | Cần tự động hoá (Argo Rollouts, Flagger) |

- ⚠️ Canary chỉ có ích khi có tiêu chí dừng rõ ràng.
- ⚠️ Canary 1% với traffic thấp không đủ dữ liệu để kết luận.

*Feature flag*
- *Feature flag* là công tắc trong code để bật tắt tính năng lúc chạy. Nó tách hai việc:
  - Deploy: đưa code lên, là việc kỹ thuật.
  - Release: bật cho người dùng, là quyết định sản phẩm.
- Ba loại flag:
  - Release flag: bật dần tính năng mới.
  - Ops flag, hay kill switch: tắt nhanh một tính năng khi có sự cố.
  - Experiment flag: chia người dùng để A/B test.
- ⚠️ Flag là nợ kỹ thuật:
  - Phải dọn flag cũ.
  - Tổ hợp nhiều flag thì khó test.
  - Flag lấy từ service ngoài phải có giá trị mặc định khi service đó lỗi.

**Đọc**
- Martin Fowler: [BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html), [CanaryRelease](https://martinfowler.com/bliki/CanaryRelease.html), [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html) (bài dài, đọc phần phân loại toggle)
- SRE Workbook: [Canarying Releases](https://sre.google/workbook/canarying-releases/)

**Nắm chắc khi**
- [ ] Vẽ được pipeline của project mình và chỉ ra bước nào chậm nhất, bước nào thiếu
- [ ] Với mỗi chiến lược deploy, nói được cách rollback và thời gian rollback
- [ ] Nêu được tiêu chí dừng canary cụ thể (metric, ngưỡng, thời gian quan sát)

#### 1.4 Môi trường, config, 12-factor

**Vì sao cần học:** Bug kiểu "chạy ở staging, lên production thì hỏng" thường đến từ khác biệt
giữa môi trường và từ config. 12-factor là bộ nguyên tắc nền cho app chạy trên container, và
Laravel vốn đi theo nó (`.env`, log ra stderr). Hay bị hỏi: project của bạn vi phạm 12-factor ở
đâu.

**Học gì**

*Staging*
- Staging càng giống production càng bắt được nhiều lỗi:
  - Cùng image.
  - Cùng kiểu hạ tầng.
  - Cùng phiên bản DB.
- Khác ở giá trị (URL, credential), không khác ở cấu trúc.
- ⚠️ Staging khác production (dữ liệu nhỏ, không có CDN, không có tải) thì bug hiệu năng, migration
  trên bảng lớn, timeout vẫn lọt.
- ⚠️ Copy dữ liệu production về staging phải ẩn danh PII. Staging không được gửi email, SMS hay thanh
  toán thật.

*12-factor, các ý hay hỏi*

| Nguyên tắc | Nghĩa | Ví dụ Laravel |
|---|---|---|
| Config qua môi trường | Config nằm ở env var, không hard-code | `.env`, `env()` trong file config |
| Backing service gắn qua URL | DB, Redis, queue là tài nguyên gắn qua config, đổi không cần sửa code | `DB_HOST`, `REDIS_URL` |
| Tách build, release, run | Build ra artifact. Release = artifact + config. Run = chạy release đó | Image + env của từng môi trường |
| Process stateless | Không giữ state trong process hay đĩa local | Session ở Redis, file ở S3 |
| Disposability | Khởi động nhanh, tắt êm | Graceful shutdown (module 2.6) |
| Dev/prod parity | Dev, staging, production giống nhau | Cùng image |
| Log ra stdout | App không tự quản file log | `LOG_CHANNEL=stderr` |
| Admin task chạy như process một lần | Migration, script sửa dữ liệu chạy riêng, không nằm trong app | `php artisan migrate` trong một Job |

*Config và secret*
- Config không bí mật: env var, ConfigMap (module 2.3).
- Secret: để trong *secret manager* (AWS Secrets Manager, SSM Parameter Store, Vault).
  - Đưa vào lúc chạy, không build vào image.
  - Xoay vòng định kỳ (*rotation*).
  - Audit ai đã đọc.
- Validate config khi khởi động, thiếu thì fail ngay.
  - Vì sao: fail lúc deploy tốt hơn nhiều so với fail ở request đầu tiên cần tới giá trị đó.
- ⚠️ Bẫy hay gặp ([10-security.md](10-security.md)):
  - `.env` bị commit.
  - Secret in ra log lúc khởi động.
  - Cùng một secret cho mọi môi trường.

**Đọc**
- [The Twelve-Factor App](https://12factor.net/): đọc hết
- Laravel: [Deployment](https://laravel.com/docs/deployment) (phần [Optimization](https://laravel.com/docs/deployment#optimization))

**Nắm chắc khi**
- [ ] Chỉ ra được 3 chỗ project hiện tại vi phạm 12-factor và cách sửa
- [ ] Liệt kê được mọi khác biệt giữa staging và production của hệ thống mình, và bug nào có thể lọt qua mỗi khác biệt

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Workload trên Kubernetes

**Vì sao cần học:** Kubernetes là nền chạy container phổ biến nhất. Pod, Deployment, Job là các
khối cơ bản mà manifest nào cũng dùng, và debug pod lỗi là việc hàng ngày. Hay bị hỏi: debug
`CrashLoopBackOff` thế nào, sidecar là gì.

**Học gì**

*Pod*
- *Pod* là đơn vị nhỏ nhất mà Kubernetes chạy. Một pod gồm một hoặc vài container:
  - Chung network namespace, nên gọi nhau qua `localhost`.
  - Dùng chung volume.
  - Ví dụ: pod web gồm Nginx và PHP-FPM, Nginx gọi FPM qua `127.0.0.1:9000`.
- Pod là tạm thời. Pod chết thì Kubernetes tạo pod mới với IP mới. Vì vậy không gọi pod bằng IP mà
  qua Service (module 2.2).

*ReplicaSet và Deployment*
- *ReplicaSet* giữ đủ N pod: pod nào chết thì tạo lại.
- *Deployment* quản lý ReplicaSet:
  - Mỗi lần đổi image, Deployment tạo ReplicaSet mới và chuyển dần pod sang (rolling update,
    module 2.6).
  - Rollback bằng `kubectl rollout undo`.

*Init container và sidecar*
- *Init container* chạy xong trước khi container app bắt đầu. Ví dụ: chờ DB sẵn sàng.
- *Sidecar* là container phụ chạy cạnh app suốt đời pod. Ví dụ: proxy, log shipper.
- ⚠️ Sidecar kiểu cũ là một container thường. Job chỉ `Complete` khi mọi container dừng, mà sidecar
  thì chạy mãi, nên Job không bao giờ xong.
- **Native sidecar** (GA từ 1.33): khai báo trong `initContainers` với `restartPolicy: Always`.
  - Khởi động trước app.
  - Tắt sau app.
  - Không chặn Job hoàn thành.

*Job và CronJob*
- *Job* chạy một việc tới khi xong. Các tham số chính:
  - `backoffLimit`: số lần retry khi lỗi.
  - `activeDeadlineSeconds`: thời gian chạy tối đa.
  - `completions`: số lần phải chạy thành công.
  - `parallelism`: số pod chạy song song.
- *CronJob* tạo Job theo lịch:
  - `concurrencyPolicy: Forbid`: lần trước chưa xong thì bỏ qua lần này, không chạy chồng.
  - `startingDeadlineSeconds`: lỡ giờ chạy quá N giây thì bỏ qua.
  - `timeZone` (GA từ 1.27): ví dụ `Asia/Ho_Chi_Minh`. Không đặt thì lịch tính theo timezone của
    kube-controller-manager.
- ⚠️ CronJob có thể không chạy, hoặc (hiếm) chạy hai lần. Vì vậy job phải *idempotent*: chạy hai
  lần cho cùng kết quả như chạy một lần.

*Tổ chức và đóng gói*
- *Namespace* tách môi trường hoặc team trong một cluster.
  - ResourceQuota: trần tổng tài nguyên của cả namespace.
  - LimitRange: giá trị mặc định và giới hạn cho từng pod, từng container.
- Ở mức biết dùng:
  - Helm: template + file values, đóng gói thành *chart*.
  - Kustomize: *overlay* YAML, tức một bộ file gốc cộng phần vá riêng cho từng môi trường.

*Debug*
- `CrashLoopBackOff` là trạng thái container liên tục crash. Kubernetes chờ lâu dần giữa các lần
  khởi động lại.
- Các lệnh:
  - `kubectl describe pod`: events và exit code. Ví dụ exit code 137 là bị SIGKILL, hay gặp khi bị
    OOMKilled.
  - `kubectl logs --previous`: log của lần chạy trước, trước khi crash.
  - `kubectl get events`.
  - `kubectl top`: CPU và RAM đang dùng.
  - `kubectl debug`: gắn *ephemeral container* (container tạm có shell và công cụ) vào pod dùng image
    distroless không có shell.

**Đọc**
- Kubernetes: [Pods](https://kubernetes.io/docs/concepts/workloads/pods/), [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), [Sidecar Containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/), [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/), [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) (mục [Time zones](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/#time-zones))
- [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/), [kubectl Quick Reference](https://kubernetes.io/docs/reference/kubectl/quick-reference/)
- [Helm docs](https://helm.sh/docs/), [Kustomize](https://kubectl.docs.kubernetes.io/)

**Nắm chắc khi**
- [ ] Debug được một pod `CrashLoopBackOff` chỉ bằng `describe` và `logs --previous`
- [ ] Giải thích được vì sao sidecar kiểu cũ (container thường) làm Job không bao giờ `Complete`, và native sidecar sửa thế nào
- [ ] Viết được CronJob chạy lúc 2 giờ sáng giờ Việt Nam, không chạy chồng

#### 2.2 Service, Ingress, Gateway API

**Vì sao cần học:** Pod đổi IP liên tục, nên mọi traffic, dù từ trong cluster hay từ Internet,
đều đi qua Service và Ingress/Gateway. Mảng này đang thay đổi: ingress-nginx đã retire và Gateway
API là hướng chính, nên nhiều cluster cũ có việc phải chuyển. Hay bị hỏi: pod đang chạy mà không
nhận được traffic thì kiểm tra gì.

**Học gì**

*Service*
- *Service* là một địa chỉ ổn định (tên DNS + IP ảo) đứng trước một nhóm pod.
- Service chọn pod bằng *label selector*. Chỉ pod **ready** mới vào *endpoint*, tức danh sách pod
  thật sự nhận traffic.
- Pod chạy mà không nhận traffic thường vì: readiness fail, selector sai, hoặc port sai.

| Loại | Dùng cho |
|---|---|
| `ClusterIP` (mặc định) | Chỉ gọi được trong cluster |
| `NodePort` | Mở một port trên mọi node, dải 30000–32767 |
| `LoadBalancer` | Tạo một LB của cloud trỏ vào Service |
| Headless (`clusterIP: None`) | DNS trả về IP của từng pod, dùng cho StatefulSet |

- ⚠️ Mỗi Service `LoadBalancer` là một LB cloud tính tiền riêng. Gom lại qua Ingress hoặc Gateway.
- DNS trong cluster: `<service>.<namespace>.svc.cluster.local`, ví dụ
  `mysql.prod.svc.cluster.local`.

*Ingress*
- *Ingress* là rule L7 (tầng HTTP, theo host và path) trỏ tới Service.
  - Ví dụ: `api.shop.vn/orders` → Service `orders`.
- Ingress chỉ là khai báo. Cần một *controller*, tức chương trình thật sự nhận traffic và áp rule.
- API Ingress vẫn được hỗ trợ nhưng đã đóng băng tính năng.
- ⚠️ **ingress-nginx** (dự án `kubernetes/ingress-nginx`) đã retire từ 03/2026: không còn release,
  bugfix hay bản vá bảo mật. Cluster còn dùng phải lên kế hoạch chuyển.
  - Đừng nhầm với NGINX Ingress Controller của F5/NGINX. Đó là dự án khác, vẫn được bảo trì.

*Gateway API*
- **Gateway API** là hướng chính cho traffic vào cluster. Ba resource chính:
  - `GatewayClass`: loại controller được dùng.
  - `Gateway`: điểm nhận traffic (listener, port, TLS), do người vận hành hạ tầng quản lý.
  - `HTTPRoute`: rule định tuyến, do team app viết.
- Lợi ích so với Ingress:
  - Tách vai người vận hành hạ tầng và người viết route.
  - Traffic split theo trọng số (dùng cho canary) có sẵn trong spec. Với Ingress, việc này phải
    dùng annotation riêng của từng controller.
- Controller hỗ trợ Gateway API: Envoy Gateway, Istio, Cilium, Traefik, NGINX Gateway Fabric, AWS
  Load Balancer Controller...
- Công cụ chuyển đổi từ Ingress: `ingress2gateway`.
- Chi tiết mạng (L4/L7, LB): [02-networking.md](02-networking.md).

**Đọc**
- Kubernetes: [Service](https://kubernetes.io/docs/concepts/services-networking/service/), [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/), [Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/)
- [Gateway API docs](https://gateway-api.sigs.k8s.io/): phần *Concepts*, [Migrating from Ingress](https://gateway-api.sigs.k8s.io/guides/getting-started/migrating-from-ingress/), [Implementations](https://gateway-api.sigs.k8s.io/implementations/)
- Kubernetes blog: [Ingress NGINX Retirement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/), [Statement from Steering and Security Response Committees](https://kubernetes.io/blog/2026/01/29/ingress-nginx-statement/)
- [ingress2gateway](https://github.com/kubernetes-sigs/ingress2gateway)

**Nắm chắc khi**
- [ ] Viết được `Gateway` + `HTTPRoute` chia 90/10 traffic giữa hai Service
- [ ] Giải thích được vì sao pod đang chạy mà Service không gửi traffic tới (readiness, selector sai, port sai)
- [ ] Lập được kế hoạch chuyển một cluster đang dùng ingress-nginx sang Gateway API, kể cả annotation không có tương đương

#### 2.3 ConfigMap và Secret

**Vì sao cần học:** App Laravel nào cũng cần config và secret (DB password, API key). Hiểu sai
Secret của Kubernetes dẫn tới tưởng đã mã hoá, trong khi ai có quyền đọc cũng thấy. Hay bị hỏi:
Secret có an toàn không, đổi ConfigMap thì app có nhận không.

**Học gì**

*Cách dùng*
- *ConfigMap* chứa config không bí mật. *Secret* chứa dữ liệu bí mật.
- Đưa vào pod qua env var hoặc mount thành file.

*Secret không phải mã hoá*
- ⚠️ Secret chỉ là base64. Base64 là cách biểu diễn dữ liệu bằng ký tự, ai cũng giải được bằng
  `base64 -d`. Nó không phải mã hoá.
- Cần thêm:
  - *Encryption at rest* cho etcd, tức mã hoá dữ liệu trên đĩa của etcd (DB lưu mọi trạng thái của
    cluster).
  - RBAC chặt: có quyền `get`/`list` secret là đọc được nội dung.
- Tốt hơn: External Secrets Operator hoặc Secrets Store CSI Driver kéo secret từ secret manager của
  cloud. Nguồn gốc của secret nằm ngoài cluster.

*Đổi config*
- ⚠️ Đổi ConfigMap không tự restart pod.
  - Env var chỉ được đọc lúc container khởi động.
  - File mount được cập nhật sau một lúc, nhưng app phải tự đọc lại. PHP-FPM với `config:cache` thì
    không đọc lại.
- Cách hay dùng: thêm hash của config vào annotation của pod template.
  1. Config đổi thì hash đổi.
  2. Hash đổi thì pod template đổi.
  3. Pod template đổi thì Deployment tự rollout.

  Trong Helm, annotation này thường tên là `checksum/config`:

  ```yaml
  annotations:
    checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  ```

*Credential cloud cho pod*
- Không mount access key vào pod.
- Dùng danh tính gắn với ServiceAccount của pod, cloud cấp credential tạm thời:
  - AWS: IRSA hoặc EKS Pod Identity.
  - GCP: Workload Identity.

**Đọc**
- Kubernetes: [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/), [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/), [Good practices for Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/), [Encrypting data at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [External Secrets Operator](https://external-secrets.io/), [Secrets Store CSI Driver](https://secrets-store-csi-driver.sigs.k8s.io/)
- AWS: [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)

**Nắm chắc khi**
- [ ] Đọc được nội dung một Secret bằng một lệnh `kubectl` và nói được ai trong team đang có quyền đó
- [ ] Thiết kế được luồng secret DB password từ AWS Secrets Manager tới app Laravel, kể cả lúc xoay vòng

#### 2.4 Probes

**Vì sao cần học:** Probe quyết định khi nào Kubernetes restart pod và khi nào gửi traffic tới
pod. Cấu hình sai là nguyên nhân kinh điển của restart hàng loạt, tức sự cố do chính hệ thống tự
gây ra. Module này là phần thực hành trên Kubernetes của health check ở module 1.2 của
[18-reliability-observability.md](18-reliability-observability.md).

**Học gì**

*Ba loại probe*
- Probe do *kubelet* (agent của Kubernetes trên mỗi node) gọi định kỳ.

| Probe | Hỏi gì | Fail thì |
|---|---|---|
| Startup | App khởi động xong chưa | Chưa qua thì liveness và readiness chưa chạy. Quá hạn thì restart |
| Readiness | Nhận traffic được không | Gỡ pod khỏi endpoint, không restart |
| Liveness | Process có bị kẹt không | kubelet restart container |

*Các bẫy*
- ⚠️ **Liveness kiểm tra DB/Redis.**
  1. Dependency chậm.
  2. Liveness của mọi pod cùng fail.
  3. Mọi pod restart cùng lúc.
  4. Một sự cố nhỏ thành outage toàn bộ.
- ⚠️ **Readiness kiểm tra dependency dùng chung.** DB chậm → mọi pod not ready → 503 toàn bộ, kể cả
  endpoint không cần DB.
- ⚠️ **Không có startup probe cho app khởi động chậm** (JVM, warm cache). Liveness giết app trước khi
  nó kịp lên → `CrashLoopBackOff`.
- ⚠️ **Timeout probe quá ngắn.** Khi app bận GC hoặc bị CPU throttle (module 2.5), probe timeout →
  restart ngay lúc đang chịu tải → càng tệ hơn.

*Endpoint probe*
- Rẻ.
- Không cần auth.
- Không log mỗi lần gọi.

**Đọc**
- Kubernetes: [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- Phần health check trong [18-reliability-observability.md](18-reliability-observability.md) (module 1.2)

**Nắm chắc khi**
- [ ] Viết được bộ ba probe cho một pod PHP-FPM + Nginx và giải thích từng tham số thời gian
- [ ] Tái hiện được trên cluster local: liveness gọi DB, tắt DB, quan sát restart hàng loạt

#### 2.5 Resource, QoS và autoscaling

**Vì sao cần học:** Đặt resource sai gây ra những sự cố khó hiểu: pod bị OOMKilled, pod chậm bất
thường vì bị throttle, hoặc hoá đơn cloud phình to. Với PHP-FPM còn phải tính `pm.max_children`
cho khớp memory limit. Hay bị hỏi: request khác limit thế nào, HPA scale theo gì.

**Học gì**

*Request và limit*

| | Request | Limit |
|---|---|---|
| Là gì | Mức được đảm bảo. Scheduler dùng để chọn node | Trần |
| Vượt memory | | Container bị OOMKilled |
| Vượt CPU | | Bị throttle: chậm lại, không bị kill |

- *Scheduler* là thành phần chọn node để đặt pod.
- *Throttle*: CPU limit được áp theo chu kỳ (*CFS quota*, mặc định 100 ms).
  - Ví dụ: limit 0,5 CPU nghĩa là được chạy 50 ms trong mỗi 100 ms. App dùng hết 50 ms đó trong
    20 ms đầu thì phải đứng chờ 80 ms còn lại, dù trung bình vẫn chưa chạm limit.
- ⚠️ Không đặt request thì scheduler xếp quá tay. Request quá cao thì lãng phí tiền.
- Tranh luận về CPU limit, nên nói được cả hai phía:
  - Chỉ đặt CPU request, không đặt CPU limit: tránh bị throttle, tận dụng được CPU đang rảnh của
    node.
  - Có CPU limit: hành vi dễ đoán hơn, một pod không chiếm được CPU dư của pod khác.
  - Memory thì nên đặt limit.

*QoS*

| QoS class | Điều kiện | Khi node thiếu tài nguyên |
|---|---|---|
| `Guaranteed` | Mọi container có request = limit, cho cả CPU và memory | Bị evict sau cùng |
| `Burstable` | Có đặt request hoặc limit nhưng không thoả Guaranteed | Ở giữa |
| `BestEffort` | Không đặt gì | Bị evict đầu tiên |

*Runtime phải biết limit*
- Go:
  - Go 1.25+ tự đặt `GOMAXPROCS` theo CPU limit của cgroup, và cập nhật khi limit đổi.
  - ⚠️ Chỉ đọc **limit**, không đọc request. Không đặt CPU limit thì `GOMAXPROCS` vẫn bằng số core
    của node.
  - `GOMEMLIMIT` vẫn phải đặt tay.
- Java: JVM nhận biết container từ lâu. Chỉnh `MaxRAMPercentage` để chọn phần RAM dành cho heap.
- PHP-FPM: `pm.max_children × bộ nhớ mỗi worker` phải nằm dưới memory limit.

*HPA*
- *HPA* (Horizontal Pod Autoscaler) đổi số replica theo:
  - CPU hoặc memory so với **request** (không phải limit).
  - Hoặc custom metric: request/giây, độ dài queue qua *KEDA* (công cụ autoscale theo nguồn sự kiện
    như queue).
- Ví dụ: request CPU 250m, target 70%. Trung bình mỗi pod dùng quá 175m thì HPA thêm pod.
- ⚠️ Không đặt request thì HPA theo CPU không hoạt động, vì không có mẫu số để tính phần trăm.
- ⚠️ Scale mất thời gian: pull image, khởi động, warm up. Nó không cứu được spike vài giây. Giữ
  `minReplicas` đủ lớn.
- ⚠️ Scale app mà DB không scale thì nhiều pod hơn chỉ làm cạn connection DB nhanh hơn
  ([03-database-sql.md](03-database-sql.md), module 2.7).

*Node autoscaling*
- Là một lớp riêng: Cluster Autoscaler, Karpenter thêm node khi cần.
- Không có node còn chỗ thì pod nằm ở trạng thái `Pending`.

**Đọc**
- Kubernetes: [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/), [Pod Quality of Service Classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/), [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- Go blog: [Container-aware GOMAXPROCS](https://go.dev/blog/container-aware-gomaxprocs)
- [KEDA](https://keda.sh/), [Karpenter](https://karpenter.sh/)

**Nắm chắc khi**
- [ ] Tính được `pm.max_children` hợp lý cho pod có memory limit 1Gi, dựa trên bộ nhớ đo được của một worker
- [ ] Giải thích được vì sao pod chưa chạm CPU limit trung bình mà latency vẫn tăng (throttle theo chu kỳ CFS)
- [ ] Nói được HPA scale theo CPU có vấn đề gì với queue worker, và vì sao KEDA theo độ dài queue hợp hơn

#### 2.6 Rolling update và graceful shutdown

**Vì sao cần học:** "Deploy không downtime" là yêu cầu mặc định, nhưng rất nhiều hệ thống vẫn có
vài lỗi 502 mỗi lần deploy mà không ai hiểu vì sao. Nguyên nhân nằm ở trình tự tắt pod. Hay bị
hỏi: vẽ dòng thời gian từ lúc xoá pod tới lúc process thoát.

**Học gì**

*Rolling update*
- Hai tham số, mặc định 25% mỗi cái:
  - `maxSurge`: số pod được tạo thêm vượt quá số replica.
  - `maxUnavailable`: số pod được phép thiếu so với số replica.
  - Ví dụ 4 replica: tối đa 5 pod cùng lúc, tối thiểu 3 pod sẵn sàng.
- Pod mới phải ready thì rollout mới đi tiếp.
- Trong lúc rollout, bản cũ và bản mới chạy song song. Vì vậy API, message format và schema DB phải
  tương thích hai chiều.

*Chuyện gì xảy ra khi xoá pod*
- Hai việc xảy ra **song song**:
  - kubelet gửi SIGTERM tới container.
  - Control plane gỡ pod khỏi endpoint. *kube-proxy* (thành phần định tuyến Service trên mỗi node)
    và LB chỉ cập nhật sau một lúc.
- ⚠️ Vì song song nên có một khoảng thời gian app đã nhận SIGTERM mà LB vẫn gửi request tới. App tắt
  listener ngay khi nhận SIGTERM → 502 hoặc connection refused mỗi lần deploy.

*Tắt êm đúng cách*
1. `preStop` chờ vài giây để endpoint kịp được gỡ khỏi LB.
2. App nhận SIGTERM.
3. Ngừng nhận request mới.
4. Làm nốt các request đang chạy.
5. Đóng kết nối.
6. Exit.

- `lifecycle.preStop.sleep.seconds` (sleep action, GA từ 1.34, bật mặc định từ 1.30): không cần
  binary `sleep` trong image, hợp với distroless.
- Tổng preStop + thời gian drain phải nhỏ hơn `terminationGracePeriodSeconds` (mặc định 30 giây).
  Quá hạn thì bị SIGKILL.
- Job dài (ví dụ import file) cần grace period dài hơn, hoặc checkpoint để làm tiếp từ chỗ dừng.

```yaml
spec:
  terminationGracePeriodSeconds: 45
  containers:
    - name: api
      lifecycle:
        preStop:
          sleep: { seconds: 10 }      # chờ endpoint được gỡ khỏi LB
      readinessProbe:
        httpGet: { path: /ready, port: 8080 }
        periodSeconds: 5
      resources:
        requests: { cpu: "250m", memory: "256Mi" }
        limits: { memory: "512Mi" }
```

*Zero-downtime cần đủ cả năm thứ*
- Nhiều replica.
- Readiness đúng.
- Graceful shutdown.
- Migration tương thích ngược (module 3.3).
- Session không nằm trong process.

**Đọc**
- Kubernetes: [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) (mục [Termination of Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination)), [Container Lifecycle Hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/) (mục [Hook handler implementations](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/#hook-handler-implementations)), [Rolling Update Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment)
- learnk8s: [Graceful shutdown in Kubernetes](https://learnk8s.io/graceful-shutdown): **đọc hết**, có hình dòng thời gian

**Nắm chắc khi**
- [ ] Vẽ được dòng thời gian từ `kubectl delete pod` tới lúc process exit, có cả LB và kube-proxy
- [ ] Tái hiện được lỗi 502 khi rollout không có preStop (chạy `hey`/`wrk` trong lúc rollout), rồi sửa
- [ ] Tính được `terminationGracePeriodSeconds` cho service có request dài nhất 20 giây

#### 2.7 Tầng PHP: PHP-FPM, queue và runtime trong container

**Vì sao cần học:** Module riêng cho người làm PHP. PHP-FPM có mô hình process và signal khác app
Go/Java chỉ gồm một binary, nên nhiều mặc định của Kubernetes không tự đúng. Đa số lỗi deploy
Laravel trên Kubernetes (request bị cắt, config sai môi trường, job chạy hai lần) nằm ở module này.

**Học gì**

*Một hay hai container*

| Cách | Mô tả | Lưu ý |
|---|---|---|
| Hai container trong một pod | Nginx + PHP-FPM, nói chuyện qua `127.0.0.1:9000` hoặc unix socket trên `emptyDir` | Mỗi container một process, signal rõ ràng. ⚠️ Nginx cần file tĩnh trong `public/`: build vào image Nginx, hoặc copy sang volume chung lúc khởi động |
| Một container, supervisord | Chạy cả Nginx và FPM dưới supervisord | Đơn giản, nhưng PID 1 là supervisor, phải cấu hình chuyển signal và log cẩn thận |
| FrankenPHP hoặc RoadRunner | Một process phục vụ HTTP trực tiếp (FrankenPHP là Caddy + PHP trong một binary) | Không cần Nginx riêng |

*Image và OPcache*
- Base `php:8.x-fpm` (Debian) hoặc `-alpine`.
- Cài extension bằng `docker-php-ext-install`.
- `composer install --no-dev --optimize-autoloader` ở stage build.
- Chạy non-root.
- *OPcache* lưu bytecode PHP đã biên dịch trong bộ nhớ chia sẻ, để không phải biên dịch lại mỗi
  request.
- Code trong image là bất biến, nên đặt `opcache.validate_timestamps=0`: PHP không `stat` (kiểm tra
  thời gian sửa) file mỗi request.
  - Deploy là image mới, nên không cần reset cache như kiểu deploy cũ bằng symlink (đổi symlink
    `current` sang thư mục release mới).
- ⚠️ Môi trường dev bind mount source thì phải để `validate_timestamps=1`, không thì sửa code mà
  không thấy thay đổi.
- Đặt đủ `opcache.memory_consumption` và `opcache.max_accelerated_files`. Preloading là tuỳ chọn.

*Laravel optimize*
- `php artisan optimize` tạo cache cho config, route, view, event.
- ⚠️ `config:cache` lúc build image sẽ đóng băng env của môi trường build.
  1. Dockerfile chạy `config:cache`, lúc đó env là của máy build.
  2. Mọi giá trị được gộp vào `bootstrap/cache/config.php` nằm trong image.
  3. Khi có config cache, Laravel dùng thẳng file đó, không đọc lại env. Staging chạy với giá trị
     của lúc build.
- Cách sửa: chạy lúc container khởi động, hoặc đảm bảo chỉ file config mới gọi `env()`.

*Graceful shutdown của PHP-FPM*

| Signal | PHP-FPM làm gì |
|---|---|
| `SIGQUIT` | Tắt êm: chờ các request đang chạy xong |
| `SIGTERM`, `SIGINT` | Tắt ngay |

- Image chính thức `php:*-fpm` đặt `STOPSIGNAL SIGQUIT` (lệnh Dockerfile chọn signal gửi khi stop
  container).
- ⚠️ Tự build từ base khác hoặc bọc bằng script thì phải kiểm tra lại. Không thì mỗi lần deploy cắt
  ngang request.
- `process_control_timeout`: thời gian master chờ worker xong việc.
- Nginx cũng tắt êm bằng `SIGQUIT`.
- Cả hai container cần preStop sleep (module 2.6).

*Queue worker, scheduler, migration*
- Queue worker chạy bằng một Deployment riêng, cùng image, lệnh
  `php artisan queue:work --max-jobs=... --max-time=...`.
- Worker nhận SIGTERM thì làm nốt job hiện tại rồi thoát. Việc này cần extension `pcntl`.
- `terminationGracePeriodSeconds` phải lớn hơn `--timeout` của job dài nhất.
- ⚠️ `retry_after` của queue connection phải lớn hơn `--timeout`. Không thì job đang chạy bị worker
  khác nhận lại.
  - Ví dụ: job chạy 120 giây, `retry_after` là 90. Tới giây 90, queue coi job đã mất và giao cho
    worker khác. Job chạy hai lần.
- Ngoài Kubernetes (dùng Supervisor):
  - `php artisan queue:restart` báo worker thoát sau job hiện tại để nạp code mới.
  - Horizon dùng `horizon:terminate`.
- Worker là process sống lâu, nên gặp rò bộ nhớ và connection DB chết. `--max-jobs`/`--max-time` cho
  worker tự thoát và được tạo lại định kỳ.

- Scheduler, chọn một trong hai:
  - Một replica chạy `schedule:work`.
  - CronJob gọi `schedule:run` mỗi phút.
- ⚠️ Scale scheduler nhiều replica thì task chạy trùng. `onOneServer()` cần cache dùng chung (Redis).
- Migration: chạy một lần bằng Job, hoặc bằng một bước riêng trong pipeline.
  - `migrate --force`, thêm `--isolated` để có lock.
  - Không chạy trong entrypoint của mọi pod.

*Health check và log*
- FPM nói *FastCGI* (giao thức Nginx dùng để gọi FPM), không nói HTTP. Vì vậy probe `httpGet` không
  gọi thẳng FPM được.
  - Liveness: dùng `ping.path` qua `cgi-fcgi` (script php-fpm-healthcheck).
  - Readiness: đi qua Nginx tới một route nhẹ như `/up`.
- Log:
  - `error_log = /proc/self/fd/2`: ghi thẳng ra stderr của process.
  - `catch_workers_output = yes`: gom output của worker về log của master.
  - `decorate_workers_output = no`: không thêm tiền tố vào mỗi dòng, để log JSON còn nguyên.
  - Laravel: `LOG_CHANNEL=stderr`.

*Runtime chạy lâu*
- Octane (chạy trên Swoole, RoadRunner hoặc FrankenPHP) giữ app trong RAM giữa các request, nên
  nhanh hơn nhiều.
- ⚠️ Cái giá:
  - State rò giữa các request, qua singleton và biến static.
  - Rò bộ nhớ. Dùng `--max-requests` để worker tự làm mới.
- Đối chiếu: đây là mô hình mặc định của Go và Java.

**Đọc**
- Docker Hub: [php official image](https://hub.docker.com/_/php) (phần *How to install more PHP extensions*, *Configuration*); [Dockerfile php-fpm](https://github.com/docker-library/php/blob/master/8.4/bookworm/fpm/Dockerfile) (xem dòng `STOPSIGNAL`)
- PHP: [OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php) (mục [validate_timestamps](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.validate-timestamps)), [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (mục [ping.path](https://www.php.net/manual/en/install.fpm.configuration.php#ping.path), [process_control_timeout](https://www.php.net/manual/en/install.fpm.configuration.php#process-control-timeout))
- [php-fpm-healthcheck](https://github.com/renatomefi/php-fpm-healthcheck)
- Laravel: [Queue workers and deployment](https://laravel.com/docs/queues#queue-workers-and-deployment), [Worker timeouts](https://laravel.com/docs/queues#worker-timeouts), [Supervisor configuration](https://laravel.com/docs/queues#supervisor-configuration), [Octane](https://laravel.com/docs/octane) (mục [Managing memory leaks](https://laravel.com/docs/octane#managing-memory-leaks)), [Scheduling](https://laravel.com/docs/scheduling)
- [FrankenPHP docs](https://frankenphp.dev/docs/) (mục [worker mode](https://frankenphp.dev/docs/worker/)), [RoadRunner docs](https://docs.roadrunner.dev/)
- Runtime PHP-FPM chi tiết: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Chứng minh được bằng thí nghiệm: gửi `SIGTERM` và `SIGQUIT` cho PHP-FPM đang có request 10 giây, kết quả khác nhau thế nào
- [ ] Viết được manifest cho app Laravel gồm: pod web (Nginx + FPM), Deployment queue worker, scheduler, Job migration
- [ ] Giải thích được vì sao `config:cache` trong Dockerfile làm staging đọc DB của môi trường build
- [ ] Tính được grace period cho queue worker có job dài nhất 5 phút, kèm `retry_after`

#### 2.8 CI nâng cao: cache, secret, quality gate

**Vì sao cần học:** Pipeline CI có quyền deploy lên production, nên nó là mục tiêu tấn công hấp
dẫn. Ở mức mid trở lên, bạn được hỏi cách giữ CI nhanh (cache), an toàn (secret, OIDC), và cách
đặt quality gate mà mọi người không tìm cách lách.

**Học gì**

*Cache*
- Cache dependency theo hash của lockfile (`composer.lock`, `go.sum`, `package-lock.json`). Lockfile
  đổi thì hash đổi, cache tự bị bỏ.
- Cache layer Docker: registry cache, BuildKit.
- ⚠️ Cache key sai thì dùng dependency cũ, dẫn tới "chạy ở CI được mà local không", hoặc ngược lại.

*Secret trong CI*
- Dùng secret store của CI. Secret được *mask* (che đi khi in ra log) và giới hạn phạm vi theo môi
  trường hoặc branch.
- **OIDC federation**: CI xin credential tạm thời từ cloud, không lưu access key dài hạn. Với
  GitHub Actions và AWS:
  1. Job CI xin GitHub một token OIDC, là token có chữ ký chứng nhận "tôi là job của repo X,
     branch Y".
  2. Job gửi token đó cho AWS để assume một IAM role.
  3. AWS kiểm tra *trust policy* của role rồi cấp credential tạm thời.
- Giới hạn role theo repo và branch trong trust policy.
- ⚠️ Các đường lộ secret:
  - Pull request từ fork không được có secret.
  - `set -x` hoặc lệnh `env` in secret ra log.
  - Third-party action chạy với quyền của pipeline. Pin theo commit SHA, vì tag có thể bị chủ repo
    trỏ sang code khác.

*Quality gate*
- *Quality gate* là điều kiện bắt buộc trước khi merge hoặc deploy:
  - Test xanh.
  - Lint qua.
  - Không có CVE nghiêm trọng.
  - Review được duyệt.
  - Migration được review.
- ⚠️ Gate chặt nhưng flaky thì mọi người học cách bỏ qua. Test *flaky* (lúc pass lúc fail mà code
  không đổi) phải được sửa hoặc cách ly ([20-testing-quality.md](20-testing-quality.md)).
- Config khác theo môi trường đưa vào lúc deploy, không build vào image.

**Đọc**
- GitHub: [OpenID Connect](https://docs.github.com/en/actions/concepts/security/openid-connect), [Configuring OIDC in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws), [Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)

**Nắm chắc khi**
- [ ] Cấu hình được GitHub Actions deploy lên AWS bằng OIDC, không có access key nào trong repo
- [ ] Chỉ ra được trong pipeline hiện tại chỗ nào một PR độc hại có thể đọc được secret

#### 2.9 Terraform và Ansible

**Vì sao cần học:** Hạ tầng tạo bằng tay trên console thì không tái tạo được và không review
được. *IaC* (infrastructure as code) là nền cho nhiều môi trường giống nhau và cho DR. Terraform
là công cụ phổ biến nhất, và state là phần hay bị hỏi cũng như hay gây sự cố nhất.

**Học gì**

*Terraform làm việc thế nào*
- Khai báo trạng thái mong muốn bằng *HCL* (ngôn ngữ cấu hình của Terraform).
- *Provider* là plugin nói chuyện với API của cloud.
- Quy trình:
  1. `plan`: so trạng thái mong muốn với state và với thực tế, in ra sẽ tạo, sửa, xoá những gì.
  2. Người đọc kỹ plan.
  3. `apply`: thực hiện.
- ⚠️ Đọc plan kỹ. `must be replaced` với một DB nghĩa là xoá rồi tạo lại, tức mất dữ liệu.

*State*
- *State* là file ánh xạ resource trong code với resource thật trên cloud.
- Lưu remote (S3, GCS, HCP Terraform) và có *locking*, để hai người không `apply` cùng lúc làm hỏng
  state.
  - S3 backend: `use_lockfile = true` khoá bằng một file trên chính S3 (conditional write). Có từ
    1.10, ổn định từ 1.11.
  - ⚠️ Khoá bằng DynamoDB (`dynamodb_table`) đã deprecated từ 1.11 và sẽ bị bỏ. Chuyển bằng cách bật
    `use_lockfile` trước, rồi mới bỏ `dynamodb_table`.
- ⚠️ State chứa secret dạng plaintext. Phải mã hoá và giới hạn quyền truy cập bucket.
- *Drift*: ai đó sửa tay trên console làm thực tế khác code. Phát hiện bằng cách chạy `plan` định
  kỳ.

*Tổ chức code*
- Module để tái dùng.
- Tách state theo môi trường và phạm vi để giảm *blast radius*: `apply` sai ở staging không đụng tới
  production.
- `import`: đưa resource đã có sẵn vào Terraform quản lý.
- `prevent_destroy`: chặn xoá những resource quan trọng.
- OpenTofu: nhánh mã nguồn mở của Terraform sau khi Terraform đổi license. Cú pháp gần như tương
  thích.

*Ansible*

| | Terraform | Ansible |
|---|---|---|
| Làm gì | Dựng hạ tầng: VPC, VM, DB, LB | Cấu hình bên trong máy: cài package, sửa file config |
| Cách chạy | Gọi API của cloud | SSH vào máy, không cần agent |
| Idempotent | Có | Module idempotent |

- Với container và *immutable infrastructure* (không sửa máy đang chạy, chỉ thay bằng image mới),
  nhu cầu dùng Ansible giảm đi.

**Đọc**
- Terraform: [State](https://developer.hashicorp.com/terraform/language/state), [State locking](https://developer.hashicorp.com/terraform/language/state/locking), [S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3) (mục [State Locking](https://developer.hashicorp.com/terraform/language/backend/s3#state-locking))
- *Terraform: Up & Running*, 3rd ed. (Yevgeniy Brikman, O'Reilly): chương về state và module
- [Ansible: Getting started](https://docs.ansible.com/ansible/latest/getting_started/index.html)

**Nắm chắc khi**
- [ ] Đọc một `plan` và chỉ ra ngay dòng nào nguy hiểm
- [ ] Chuyển được một backend S3 từ DynamoDB lock sang `use_lockfile` mà không có lúc nào không có lock
- [ ] Giải thích được vì sao tách state production khỏi staging

---

### Chặng 3: Senior 🔴

#### 3.1 Bảo mật Kubernetes

**Vì sao cần học:** Mặc định Kubernetes khá "mở": pod chạy root được, mọi pod gọi được mọi pod,
token gọi API server được mount sẵn vào pod. Một pod bị chiếm có thể thành bàn đạp để chiếm cả
cluster. Senior được hỏi các lớp phòng thủ và các đường leo quyền.

**Học gì**

*securityContext*
- Đặt cho mỗi container:
  - `runAsNonRoot: true`, `runAsUser` cụ thể.
  - `readOnlyRootFilesystem: true`.
    - ⚠️ Laravel cần ghi `storage/` và `bootstrap/cache`. Mount `emptyDir` riêng cho hai chỗ đó.
  - `allowPrivilegeEscalation: false`: process con không được có quyền cao hơn process cha, ví dụ
    qua binary setuid.
  - `capabilities.drop: ["ALL"]`. *Capability* là quyền của root được chia nhỏ, ví dụ quyền bind
    port thấp, quyền đổi owner file.
  - `seccompProfile.type: RuntimeDefault`: lọc bớt các syscall nguy hiểm.

```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities: { drop: ["ALL"] }
  seccompProfile: { type: RuntimeDefault }
```

*Pod Security Admission*
- Thay PodSecurityPolicy, đã bị bỏ ở 1.25.
- Gắn label cho namespace `pod-security.kubernetes.io/enforce` với một trong ba mức:
  - `privileged`: không hạn chế.
  - `baseline`: chặn các cấu hình nguy hiểm rõ ràng.
  - `restricted`: chặt nhất.
- Có chế độ `audit` và `warn` để thử trước khi `enforce`.

*NetworkPolicy*
- Mặc định mọi pod gọi được mọi pod.
- Đặt *default-deny* (chặn hết) rồi mở từng luồng: web → DB, worker → Redis.
- ⚠️ Chỉ có tác dụng khi CNI (plugin mạng của cluster) hỗ trợ, như Calico, Cilium. CNI không hỗ trợ
  thì policy vẫn tồn tại mà không chặn gì.
- ⚠️ Default-deny egress mà quên mở DNS (port 53 tới CoreDNS) thì mọi thứ hỏng.

*RBAC*
- *RBAC* gồm:
  - Role (quyền trong một namespace) hoặc ClusterRole (quyền trên toàn cluster).
  - RoleBinding: gán Role cho ai.
- Mỗi app một ServiceAccount riêng.
- `automountServiceAccountToken: false` khi app không cần gọi API server.
- ⚠️ Quyền `list` secret là đọc được toàn bộ nội dung.
- ⚠️ Quyền tạo pod trong namespace gần như bằng quyền đọc mọi secret của namespace đó, vì pod tự tạo
  có thể mount bất kỳ secret nào.
- CI không dùng `cluster-admin`.

*Secret và admission policy*
- Secret: bật encryption at rest, dùng External Secrets hoặc CSI (module 2.3).
- GitOps thì dùng Sealed Secrets hoặc SOPS để mã hoá secret trước khi vào Git. Không để plaintext
  trong Git.
- *Admission policy* (Kyverno, OPA Gatekeeper) chặn resource vi phạm chính sách ngay lúc tạo. Ví dụ:
  - Chỉ cho image từ registry nội bộ.
  - Bắt buộc có resource request.
- Chi tiết bảo mật ứng dụng: [10-security.md](10-security.md).

**Đọc**
- Kubernetes: [Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/), [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/), [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/), [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/), [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/), [RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) (mục privilege escalation), [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets), [SOPS](https://github.com/getsops/sops)

**Nắm chắc khi**
- [ ] Chạy được app Laravel ở namespace `restricted` với `readOnlyRootFilesystem: true`
- [ ] Viết được bộ NetworkPolicy default-deny cho namespace có web, worker, Redis, và chứng minh DNS vẫn chạy
- [ ] Kể được 3 đường một pod bị chiếm quyền có thể leo sang toàn cluster, và cách chặn mỗi đường

#### 3.2 PodDisruptionBudget, StatefulSet, scheduling

**Vì sao cần học:** Nâng cấp cluster và drain node là việc định kỳ. Không có PDB và topology
spread thì một lần drain có thể tắt mọi replica cùng lúc. StatefulSet gắn với câu hỏi hay gặp "có
nên chạy DB trên Kubernetes không".

**Học gì**

*Gián đoạn tự nguyện và không tự nguyện*

| | Tự nguyện | Không tự nguyện |
|---|---|---|
| Ví dụ | Drain node, nâng cấp cluster | Node chết, OOM |
| PDB bảo vệ được | Có | ⚠️ Không |

- *Drain* node là đuổi hết pod khỏi node để bảo trì.

*PodDisruptionBudget*
- *PDB* giới hạn số pod bị gián đoạn **tự nguyện** cùng lúc, bằng `minAvailable` hoặc
  `maxUnavailable`.
  - Ví dụ: 3 replica, `maxUnavailable: 1`. Drain chỉ đuổi từng pod một, chờ pod thay thế ready rồi
    mới đuổi pod tiếp.
- ⚠️ PDB `minAvailable` bằng đúng số replica thì drain node treo mãi, chặn luôn việc nâng cấp
  cluster.

*Rải replica*
- *Anti-affinity*: không đặt hai replica lên cùng node.
- *Topology spread constraints*: rải đều replica theo node hoặc AZ.
- Mục tiêu: một node hay một AZ chết không mang theo mọi replica.

*StatefulSet*
- Dành cho workload cần danh tính ổn định:
  - Tên và thứ tự ổn định: `db-0`, `db-1`.
  - Mỗi pod một *PersistentVolume* (ổ đĩa bền) riêng.
  - DNS ổn định qua headless Service.
  - Khởi động và tắt theo thứ tự.
- ⚠️ Tự chạy DB trên Kubernetes là tự gánh backup, failover, nâng cấp. Nhiều team chọn managed DB
  cho production.

**Đọc**
- Kubernetes: [Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/), [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/), [Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)

**Nắm chắc khi**
- [ ] Đặt được PDB và topology spread cho Deployment 3 replica chạy trên 3 AZ, và giải thích điều gì xảy ra khi drain một node
- [ ] Bảo vệ được quyết định dùng RDS thay vì MySQL trên StatefulSet

#### 3.3 Migration khi deploy và rollback dữ liệu

**Vì sao cần học:** Code rollback thì dễ, dữ liệu thì không. Mọi chiến lược deploy không downtime
đều có lúc bản cũ và bản mới cùng chạy trên một DB, nên migration phải được thiết kế cho lúc đó.
Hay bị hỏi: đổi tên cột thế nào mà không downtime.

**Học gì**

*Vì sao migration là vấn đề*
- Trong rolling hay blue-green, bản cũ và bản mới chạy trên cùng một DB.
- Migration không tương thích ngược làm bản cũ lỗi ngay.
  - Ví dụ: migration đổi tên cột `name` thành `full_name`. Pod bản cũ vẫn `SELECT name`, lỗi ngay khi
    migration chạy xong.

*Expand/contract*
- Còn gọi là *parallel change*. Ví dụ đổi `name` → `full_name`:
  1. Expand: thêm cột `full_name` nullable. Deploy code ghi cả hai cột, vẫn đọc cột cũ.
  2. Backfill: chép dữ liệu cũ sang cột mới theo batch nhỏ.
  3. Deploy code đọc cột mới, vẫn ghi cả hai.
  4. Deploy code chỉ dùng cột mới.
  5. Contract: xoá cột cũ ở một lần deploy sau, khi chắc chắn không cần rollback nữa.
- Quy tắc thứ tự:
  - Migration tương thích ngược chạy **trước** code mới.
  - Contract chạy **sau**, khi code cũ không còn chạy ở đâu.

*Migration nguy hiểm trên bảng lớn*
- ⚠️ Các thao tác có thể khoá hoặc viết lại cả bảng:
  - Thêm cột `NOT NULL` không có default.
  - Thêm index trên bảng lớn.
  - Đổi kiểu cột.
- Dùng online DDL hoặc gh-ost ([03-database-sql.md](03-database-sql.md), module 3.3).

*Chạy migration ở đâu*
- ⚠️ Chạy migration từ mỗi pod lúc khởi động thì nhiều pod cùng chạy một lúc.
- Chạy một lần, có lock (module 2.7).

*Rollback dữ liệu*
- Rollback code dễ, rollback **data** khó. Những thứ không quay lại được:
  - Cột đã xoá.
  - Email đã gửi.
  - Message đã publish theo format mới.
- Đôi khi *roll forward* (sửa tiếp bằng một bản mới) an toàn hơn rollback.
- Thay đổi config cũng là deploy: có version, có review, rollback được.

**Đọc**
- Martin Fowler: [ParallelChange](https://martinfowler.com/bliki/ParallelChange.html)
- Module 3.3 của [03-database-sql.md](03-database-sql.md)

**Nắm chắc khi**
- [ ] Lập được kế hoạch tách `address` text thành bảng `addresses` (bài tập 3), mỗi bước ghi rollback thế nào
- [ ] Liệt kê được 3 thay đổi không rollback được trong một lần deploy bình thường và cách giảm rủi ro

#### 3.4 GitOps và supply chain

**Vì sao cần học:** Câu "production đang chạy đúng commit nào" nghe đơn giản, nhưng nhiều team
không trả lời được. GitOps giúp trả lời câu đó, còn supply chain security chứng minh image đang
chạy đúng là image team đã build, không bị ai chèn gì vào.

**Học gì**

*GitOps*
- *GitOps*: Git là nguồn sự thật cho trạng thái cluster.
- Một agent chạy trong cluster (Argo CD, Flux) kéo manifest từ Git về và đồng bộ. Cluster lệch so
  với Git thì agent báo hoặc tự sửa.
- Mô hình pull này có các lợi ích:
  - CI không cần credential vào cluster.
  - Mọi thay đổi có review và lịch sử.
  - Rollback = revert commit.
- Hay tách hai repo:
  1. Repo code: CI build image.
  2. Repo manifest: CI cập nhật tag image mới vào đây, agent đồng bộ vào cluster.
- ⚠️ Sửa tay bằng `kubectl` sẽ bị ghi đè ở lần sync tiếp theo.

*Tag image*
- ⚠️ `:latest` hoặc tag bị ghi đè thì không biết đang chạy bản nào.
- Tag theo git SHA hoặc version.
- Production pin theo digest `@sha256:...`, vì digest không thể trỏ sang nội dung khác.

*Supply chain*
- *Supply chain* là chuỗi từ code, dependency tới image chạy trên production. Các lớp bảo vệ:
  - Scan *CVE* (lỗ hổng đã được công bố) bằng Trivy, Grype.
  - *SBOM* (software bill of materials): danh sách mọi thành phần có trong image.
  - Ký image bằng cosign, và kiểm chữ ký ở admission: chỉ cho chạy image có chữ ký hợp lệ.

**Đọc**
- [OpenGitOps principles](https://opengitops.dev/), [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/) (phần *Core Concepts*)
- [Trivy](https://trivy.dev/), [Sigstore cosign](https://docs.sigstore.dev/cosign/signing/overview/)

**Nắm chắc khi**
- [ ] So sánh được CI push deploy với GitOps pull theo 4 tiêu chí: credential, audit, rollback, drift
- [ ] Trả lời được "production đang chạy đúng commit nào" trong 1 phút với hệ thống của mình

#### 3.5 Dịch vụ cloud (AWS làm ví dụ)

**Vì sao cần học:** Phỏng vấn system design gần như luôn có phần "chạy trên cloud thế nào". Cần
gọi đúng tên dịch vụ, biết điểm khác nhau giữa các dịch vụ gần giống nhau, và biết các bẫy gây tốn
tiền hoặc rò dữ liệu. AWS làm ví dụ vì phổ biến nhất, bảng dưới giúp chuyển sang GCP/Azure.

**Học gì**

*Tương đương giữa các cloud*

| Nhu cầu | AWS | GCP | Azure |
|---|---|---|---|
| VM | EC2 | Compute Engine | Virtual Machines |
| Container được quản lý | ECS (Fargate), EKS | Cloud Run, GKE | Container Apps, AKS |
| Function | Lambda | Cloud Run functions | Azure Functions |
| Object storage | S3 | Cloud Storage | Blob Storage |
| DB quan hệ | RDS, Aurora | Cloud SQL, AlloyDB | Azure SQL, Azure Database for MySQL/PostgreSQL |
| Key-value/document | DynamoDB | Firestore, Bigtable | Cosmos DB |
| Cache | ElastiCache | Memorystore | Azure Cache for Redis |
| Queue / pub-sub | SQS / SNS | Pub/Sub | Service Bus, Event Grid |
| CDN, DNS | CloudFront, Route 53 | Cloud CDN, Cloud DNS | Front Door, Azure DNS |
| Danh tính | IAM | IAM | Entra ID + RBAC |
| Log, metric | CloudWatch | Cloud Logging/Monitoring | Azure Monitor |

*Region, AZ và compute*
- *Region* là một vùng địa lý (ví dụ Singapore). Mỗi region có nhiều AZ.
- Chạy ít nhất 2 AZ.
- ⚠️ Truyền dữ liệu giữa các AZ có tính phí.
- EC2:
  - Loại burstable (`t3`, `t4g`) chạy bằng *CPU credit*. Hết credit là chậm hẳn.
  - *Spot* rẻ nhưng có thể bị AWS thu hồi bất cứ lúc nào, nên hợp với worker stateless.
- ECS/Fargate đơn giản hơn Kubernetes. EKS là Kubernetes mà AWS quản lý control plane.

*S3*
- Strong read-after-write consistency từ 12/2020: ghi xong đọc ngay là thấy bản mới.
- Storage class (các mức giá theo tần suất truy cập) và lifecycle rule (tự chuyển class hoặc xoá
  theo tuổi file).
- *Presigned URL*: link có chữ ký và hạn dùng, cho client tải lên hoặc tải về trực tiếp mà không cần
  credential.
- Versioning: giữ các phiên bản cũ của file.
- ⚠️ Bucket public nhầm là nguồn rò rỉ kinh điển. Bật Block Public Access, phục vụ file qua
  CloudFront với origin access control.

*Database*
- RDS Multi-AZ khác read replica:

  | | RDS Multi-AZ | Read replica |
  |---|---|---|
  | Mục đích | Standby để failover | Bản sao để đọc |
  | Nhận traffic đọc | Không | Có |
  | Sao chép | Đồng bộ (synchronous) sang standby | Async, có lag |

- Aurora: storage tách khỏi compute, failover nhanh.
  - ⚠️ Failover đổi node đứng sau endpoint, nên app phải reconnect.
- DynamoDB: thiết kế theo access pattern.
  - ⚠️ Hot partition, scan đắt ([04-nosql-search-storage.md](04-nosql-search-storage.md)).
- ElastiCache (Redis/Valkey/Memcached): [11-cache.md](11-cache.md).

*Queue và DNS*
- SQS có hai loại:
  - Standard: at-least-once (một message có thể được giao hơn một lần), không đảm bảo thứ tự.
  - FIFO: giữ thứ tự.
- Các khái niệm SQS:
  - *Visibility timeout*: thời gian message bị ẩn khỏi consumer khác sau khi được nhận. Phải lớn hơn
    thời gian xử lý, không thì message bị xử lý hai lần.
  - DLQ (dead-letter queue): nơi chứa message lỗi quá số lần thử.
  - Long polling: chờ tới khi có message thay vì hỏi liên tục.
- SNS fan-out một message sang nhiều SQS. EventBridge định tuyến event
  ([12-messaging.md](12-messaging.md)).
- Route 53:
  - Routing policy: weighted, latency, failover.
  - Health check.
  - Alias record cho apex domain (domain gốc như `shop.vn`, không có `www`).

*IAM*
- Policy là JSON gồm `Effect`, `Action`, `Resource`, `Condition`. Deny tường minh luôn thắng allow.
- User và role:
  - User có credential dài hạn.
  - Role được *assume* (nhận vai) qua STS, dịch vụ cấp credential tạm thời của AWS.
- Người dùng đăng nhập qua SSO. App trên EC2/ECS/Lambda/EKS dùng role (instance profile, task role,
  IRSA/EKS Pod Identity).
- ⚠️ Các bẫy:
  - `"Action": "*"`, `"Resource": "*"`.
  - Access key bị commit lên Git. Bot quét được trong vài phút.
  - Tài khoản root dùng hằng ngày, không có MFA.
- Tách tài khoản AWS theo môi trường (AWS Organizations).

*Mạng và log*
- VPC, subnet, security group, NAT gateway, VPC endpoint: [02-networking.md](02-networking.md).
- CloudWatch: ⚠️ log group không đặt retention thì được lưu và tính tiền mãi mãi.

**Đọc**
- AWS: [IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html), [RDS Multi-AZ](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html), [SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html), [S3 consistency](https://aws.amazon.com/s3/consistency/), [Restricting access to S3 origin](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- AWS Well-Architected: trụ cột *Reliability* và *Security*

**Nắm chắc khi**
- [ ] Vẽ được kiến trúc AWS cho app Laravel: ALB, ECS/EKS ở 2 AZ, RDS Multi-AZ, ElastiCache, SQS, S3 + CloudFront
- [ ] Viết được IAM policy cho worker chỉ đọc/xoá message của một queue SQS và ghi vào một prefix S3
- [ ] Giải thích được RDS Multi-AZ và read replica khác nhau ở mục đích và ở RPO

#### 3.6 Serverless trade-off

**Vì sao cần học:** Serverless hấp dẫn vì không phải quản server, nhưng có những giới hạn làm nó
không hợp với mọi loại tải. Hay bị hỏi: cold start là gì, và vì sao một đợt spike trên Lambda có
thể đánh sập DB.

**Học gì**

*Ưu điểm*
- Không quản server.
- Scale về 0 khi không có request.
- Trả tiền theo mức dùng.
- Tích hợp sẵn với các nguồn sự kiện (S3, SQS, API Gateway).

*Cold start*
- *Cold start*: request đầu tiên vào một instance mới phải chờ khởi tạo runtime và code, nên chậm.
- Nặng hơn với JVM và package lớn.
- Cách giảm:
  - Provisioned concurrency: giữ sẵn một số instance đã khởi tạo.
  - SnapStart: khởi động từ snapshot đã khởi tạo sẵn.
  - Code khởi động nhẹ.

*Giới hạn*
- Lambda chạy tối đa 15 phút mỗi lần.
- Có giới hạn payload, bộ nhớ, dung lượng `/tmp`.
- API Gateway có timeout tích hợp ngắn hơn nhiều (xem trang quota hiện hành).

*Concurrency và DB*
- Mỗi instance Lambda xử lý một request một lúc.
- ⚠️ Chuỗi sự cố:
  1. Spike tới, Lambda tạo hàng nghìn instance.
  2. Mỗi instance mở kết nối DB riêng.
  3. DB cạn connection.
- Cách chặn:
  - RDS Proxy: gom kết nối từ nhiều instance vào một pool.
  - Reserved concurrency: đặt trần số instance cho function.
- Quota concurrency tính chung theo tài khoản và region.

*Chi phí và các đánh đổi khác*
- ⚠️ Rẻ với tải thấp hoặc không đều. Tải cao và đều thì container/VM thường rẻ hơn.
- Khó chạy local, khó debug, dễ bị lock-in.
- State phải nằm ngoài function.
- PHP trên Lambda: có qua runtime cộng đồng, ví dụ Bref. Cùng các giới hạn như trên.

**Đọc**
- AWS Lambda: [Quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [Concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)
- AWS: [RDS Proxy](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html)

**Nắm chắc khi**
- [ ] Tính được điểm hoà vốn giữa Lambda và container cho một API ở 50 request/giây đều đặn
- [ ] Giải thích được một đợt spike trên Lambda đánh sập RDS thế nào và 2 cách chặn

#### 3.7 Cost awareness

**Vì sao cần học:** Senior được kỳ vọng biết kiến trúc mình đề xuất tốn bao nhiêu tiền, và điều
tra được khi hoá đơn tăng bất thường. Nhiều khoản lớn nằm ở chỗ ít ai để ý, như data transfer và
NAT gateway.

**Học gì**

*Các khoản hay bị bỏ qua*
- Data transfer ra Internet, và giữa các AZ hoặc region.
- NAT gateway, tính tiền theo GB đi qua.
- Log và metric: lưu lâu, cardinality cao.
- Snapshot và volume mồ côi (không còn gắn với máy nào).
- LB không dùng tới.
- Môi trường dev chạy 24/7.
- Instance quá cỡ so với nhu cầu.

*Ví dụ kinh điển: S3 qua NAT gateway*
1. App ở private subnet (không có IP public) tải file lớn từ S3.
2. Traffic đi qua NAT gateway, bị tính tiền theo từng GB.
3. Hoá đơn NAT gateway tăng vọt.

- Cách sửa: thêm *VPC gateway endpoint* cho S3, để traffic tới S3 đi thẳng trong mạng AWS, không qua
  NAT.

*Công cụ*
- Tag tài nguyên theo team và service, để biết ai tiêu tiền.
- Budget alert.
- Cost Explorer.
- *Rightsizing*: chỉnh cỡ instance theo metric sử dụng thật.

*Mô hình giá*

| Mô hình | Là gì | Hợp với |
|---|---|---|
| On-demand | Trả theo giờ dùng, không cam kết | Tải khó đoán |
| Reserved / savings plan | Cam kết dùng 1 hoặc 3 năm để được giảm giá | Tải nền ổn định |
| Spot | Dùng capacity dư, rẻ nhưng có thể bị thu hồi | Worker stateless, batch |

- ARM (Graviton) thường rẻ hơn cho cùng hiệu năng, nhưng phải đo với workload của mình.
  - Kiểm tra extension PHP native và image multi-arch.

*Góc senior*
- Ước lượng chi phí cho mỗi 1 triệu request.
- Biết đánh đổi giữa chi phí và HA.
- Không tối ưu sớm những khoản nhỏ.

**Đọc**
- AWS: [Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html), [Gateway endpoints for S3](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html)
- [FinOps Framework](https://www.finops.org/framework/): lướt phần *Principles*

**Nắm chắc khi**
- [ ] Ước lượng được hoá đơn tháng cho kiến trúc ở bài tập 5 và chỉ ra khoản lớn nhất
- [ ] Kể được quy trình điều tra "hoá đơn tăng 40% mà traffic không đổi"

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Container khác VM thế nào?** (1.1)
- Ý phải có: chung kernel, namespace + cgroup; VM có kernel riêng trên hypervisor
- Điểm cộng: hệ quả bảo mật; microVM là điểm giữa

**2. Viết Dockerfile tốt cần lưu ý gì?** (1.1, 1.2)
- Ý phải có: thứ tự layer cho cache, multi-stage, image base nhỏ, non-root, `.dockerignore`, exec form
- Điểm cộng: secret lúc build bằng BuildKit; cài và dọn cùng một `RUN`
- Red flag: `COPY . .` ngay dòng đầu, chạy root, `:latest`

**3. Rolling, blue-green, canary khác nhau thế nào? Rollback mỗi loại ra sao?** (1.3)
- Ý phải có: cách làm, chi phí hạ tầng, tốc độ rollback của mỗi loại
- Điểm cộng: canary cần tiêu chí dừng tự động; DB dùng chung vẫn phải tương thích

**4. Feature flag giải quyết vấn đề gì?** (1.3)
- Ý phải có: tách deploy khỏi release, tắt nhanh khi lỗi, bật dần theo nhóm
- Điểm cộng: flag là nợ kỹ thuật; phân loại flag; giá trị mặc định khi flag service lỗi

**5. Vì sao không lưu dữ liệu trong container?** (1.1)
- Ý phải có: layer ghi được mất khi container bị xoá; nhiều replica không chung filesystem
- Điểm cộng: upload file của Laravel phải lên S3, session/cache lên Redis

**6. 12-factor app gồm những ý gì quan trọng nhất?** (1.4)
- Ý phải có: config qua env, stateless, log ra stdout, disposability, dev/prod parity
- Điểm cộng: liên hệ với Kubernetes (probe, SIGTERM, ConfigMap)

### 🟡 Mid

**7. `ENTRYPOINT` và `CMD` khác nhau thế nào? Shell form có vấn đề gì?** (1.2)
- Ý phải có: chương trình chính và đối số mặc định; shell form làm shell thành PID 1, SIGTERM không tới app
- Điểm cộng: `exec "$@"` trong entrypoint script; grace period rồi SIGKILL

**8. Liveness, readiness, startup probe khác nhau thế nào?** (2.4)
- Ý phải có: câu hỏi mỗi probe trả lời và hành động khi fail
- Điểm cộng: liveness không kiểm tra dependency; startup probe cho app khởi động chậm; timeout tính đến GC/throttle
- Red flag: liveness gọi DB và Redis

**9. Request và limit khác nhau thế nào? Vượt memory limit và vượt CPU limit thì sao?** (2.5)
- Ý phải có: request cho scheduler, limit là trần; OOMKilled so với throttle; QoS class
- Điểm cộng: tranh luận bỏ CPU limit; Go 1.25 đọc CPU limit để đặt `GOMAXPROCS`; PHP-FPM `max_children` theo memory limit

**10. Làm sao deploy mà người dùng không bị gián đoạn?** (2.6, 3.3)
- Ý phải có: nhiều replica, readiness đúng, graceful shutdown có preStop, migration tương thích ngược
- Điểm cộng: SIGTERM và gỡ endpoint chạy song song; API và message tương thích hai chiều; kế hoạch rollback dữ liệu
- Red flag: "dùng rolling update là đủ"

**11. Secret trong Kubernetes có an toàn không?** (2.3)
- Ý phải có: base64 không phải mã hoá; encryption at rest; RBAC
- Điểm cộng: External Secrets/CSI; quyền tạo pod gần bằng quyền đọc secret; IRSA/Pod Identity thay access key

**12. Ingress khác Gateway API thế nào? Cluster đang dùng ingress-nginx thì làm gì?** (2.2)
- Ý phải có: Ingress chỉ có rule host/path và phụ thuộc annotation của controller; Gateway API tách vai, có traffic split, route theo header; ingress-nginx đã retire từ 03/2026, không còn bản vá bảo mật
- Điểm cộng: kế hoạch chuyển (kiểm kê annotation, `ingress2gateway`, chạy song song, chuyển DNS dần); phân biệt với NGINX Ingress Controller của F5
- Red flag: không biết dự án đã dừng bảo trì

**13. Chạy Laravel trên Kubernetes: một container hay hai? OPcache cấu hình thế nào?** (2.7)
- Ý phải có: Nginx + FPM hai container chung pod, hoặc FrankenPHP một process; `validate_timestamps=0` vì code bất biến trong image
- Điểm cộng: file tĩnh cho Nginx; `config:cache` lúc khởi động chứ không lúc build; dev bind mount thì bật lại validate

**14. Deploy xong thấy vài request bị cắt ngang ở PHP-FPM. Vì sao?** (2.6, 2.7)
- Ý phải có: FPM nhận SIGTERM là tắt ngay, cần SIGQUIT; thiếu preStop nên LB còn gửi request
- Điểm cộng: `STOPSIGNAL` của image chính thức; `process_control_timeout`; grace period đủ dài

**15. Queue worker trên Kubernetes xử lý deploy thế nào để không mất job?** (2.7)
- Ý phải có: worker bắt SIGTERM làm nốt job rồi thoát; grace period > timeout của job; job idempotent
- Điểm cộng: `retry_after` > `--timeout`; `queue:restart` khi chạy bằng Supervisor; KEDA scale theo độ dài queue

**16. IAM role khác IAM user thế nào? Least privilege là gì?** (3.5, 2.8)
- Ý phải có: credential tạm thời qua STS so với dài hạn; chỉ cấp action và resource cần
- Điểm cộng: OIDC cho CI; tách tài khoản theo môi trường; condition trong policy

**17. Terraform state là gì? Drift là gì? Locking làm thế nào?** (2.9)
- Ý phải có: ánh xạ code với resource thật; remote state có lock; drift là thực tế lệch code
- Điểm cộng: S3 `use_lockfile` thay DynamoDB lock đã deprecated; state chứa secret; tách state theo môi trường

**18. Pod `CrashLoopBackOff` sau khi deploy bản mới. Làm gì?** (2.1)
- Ý phải có: rollback trước; `describe pod` (exit code, `OOMKilled`), `logs --previous`
- Điểm cộng: nguyên nhân hay gặp (thiếu config/secret, liveness giết app khởi động chậm, memory limit thấp, không ghi được filesystem chỉ đọc)

### 🔴 Senior

**19. Vì sao pod đã bắt SIGTERM mà vẫn có request lỗi lúc deploy?** (2.6)
- Ý phải có: gỡ endpoint và SIGTERM song song, LB cập nhật chậm; cần preStop chờ
- Điểm cộng: `preStop.sleep` (GA 1.34) cho image không có shell; tổng thời gian < grace period; keep-alive connection

**20. Làm migration DB tương thích ngược khi deploy thế nào?** (3.3)
- Ý phải có: expand/contract nhiều lần deploy; migration chạy trước code, contract chạy sau
- Điểm cộng: thao tác nào khoá bảng; chạy migration một lần bằng Job có lock; backfill theo batch

**21. Mỗi lần DB chậm vài giây, mọi pod API restart cùng lúc, hệ thống sập vài phút.** (2.4)
- Ý phải có: liveness đang kiểm tra DB; bỏ dependency khỏi liveness
- Điểm cộng: xem lại readiness và timeout probe; timeout/circuit breaker cho DB để app trả lỗi nhanh

**22. PodDisruptionBudget dùng để làm gì? Nó không bảo vệ khỏi cái gì?** (3.2)
- Ý phải có: giới hạn gián đoạn tự nguyện; không chống node chết
- Điểm cộng: `minAvailable` bằng số replica chặn drain; kết hợp topology spread

**23. Bạn khoá bảo mật một namespace Kubernetes thế nào?** (3.1)
- Ý phải có: Pod Security Admission `restricted`, securityContext non-root và filesystem chỉ đọc, NetworkPolicy default-deny, ServiceAccount riêng quyền tối thiểu
- Điểm cộng: CNI phải hỗ trợ NetworkPolicy; nhớ mở DNS; admission policy; ký và scan image
- Red flag: "Kubernetes đã an toàn mặc định"

**24. Terraform plan báo sẽ replace RDS production chỉ vì đổi một tham số nhỏ.** (2.9)
- Ý phải có: không apply; tìm thuộc tính bắt buộc replace; tìm cách đổi tại chỗ hoặc kế hoạch migration có backup
- Điểm cộng: `prevent_destroy`, deletion protection, review plan bắt buộc trong CI

**25. Serverless có trade-off gì? Khi nào không nên dùng?** (3.6)
- Ý phải có: cold start, giới hạn thời gian, concurrency cạn connection DB, chi phí ở tải cao đều
- Điểm cộng: RDS Proxy, reserved concurrency; khó debug, lock-in

**26. GitOps khác CI push deploy thế nào?** (3.4)
- Ý phải có: pull từ trong cluster, Git là nguồn sự thật, rollback bằng revert
- Điểm cộng: CI không cần credential cluster; drift tự sửa; secret trong Git phải mã hoá

**27. Hoá đơn AWS tháng này tăng 40% mà traffic không đổi.** (3.7)
- Ý phải có: Cost Explorer theo service và tag; nghi phạm hay gặp là data transfer, NAT gateway, log, resource quên xoá
- Điểm cộng: ví dụ S3 qua NAT → VPC endpoint; budget alert, tag bắt buộc

**28. AWS access key bị lộ trên GitHub public repo.** (3.5)
- Ý phải có: vô hiệu hoá/xoay key ngay, trước khi xoá commit; CloudTrail xem key đã làm gì
- Điểm cộng: role thay access key, OIDC cho CI, secret scanning trước commit; coi là sự cố bảo mật
- Red flag: chỉ xoá commit rồi force push

**29. Có nên dùng Kubernetes không?** (2.1, 3.5)
- Ý phải có: tuỳ quy mô team và số service; Kubernetes cần người vận hành (nâng cấp, network, bảo mật)
- Điểm cộng: vài service với team nhỏ thì ECS/Cloud Run/PaaS đủ; nói được dấu hiệu nên chuyển
- Red flag: "có, vì là chuẩn"

---

## Bài tập tự làm

1. Viết Dockerfile multi-stage cho một app trong repo này (Go hoặc PHP): chạy non-root, có `.dockerignore`, exec form. Bản PHP: stage `composer install --no-dev`, image `php:8.x-fpm`, OPcache `validate_timestamps=0`. So kích thước image trước và sau khi tối ưu, giải thích từng thay đổi.
2. Viết manifest Kubernetes cho một API stateless: Deployment, Service, Gateway API `HTTPRoute` (không dùng ingress-nginx), HPA, PDB, NetworkPolicy, với probes, resource, `preStop.sleep`, securityContext. Ghi chú bên cạnh mỗi giá trị vì sao chọn con số đó.
3. Viết kế hoạch expand/contract từng bước (mỗi bước ghi migration, thay đổi code, cách rollback) để tách cột `address` dạng text thành bảng `addresses` riêng, trong khi hệ thống vẫn chạy.
4. Thiết kế pipeline CI/CD (YAML giả hoặc sơ đồ) cho một monorepo hai service: cache, test, build image một lần, scan, OIDC tới cloud, deploy staging, canary production, điều kiện dừng canary, rollback.
5. Ước lượng chi phí hàng tháng trên AWS cho một app: 2 AZ, 3 container, RDS MySQL Multi-AZ, Redis, ALB, NAT gateway, 500 GB traffic ra Internet. Ghi rõ giả định và khoản nào lớn nhất.
6. **PHP trên Kubernetes.** Trên cluster local (kind/minikube), chạy một app Laravel gồm pod web (Nginx + PHP-FPM), queue worker, scheduler và Job migration:
   - Tạo một route ngủ 10 giây, bắn tải trong lúc `kubectl rollout restart`, ghi lại số request lỗi khi FPM nhận `SIGTERM` và khi nhận `SIGQUIT` có preStop.
   - Dispatch một job chạy 60 giây rồi xoá pod worker, quan sát job có bị mất hay chạy lại không, và chỉnh grace period, `retry_after` cho đúng.

> Nộp bài vào đây để được review.
