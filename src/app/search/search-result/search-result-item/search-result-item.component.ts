import { Component, OnInit, TemplateRef } from '@angular/core';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-search-result-item',
  templateUrl: './search-result-item.component.html',
  styleUrls: ['./search-result-item.component.css']
})
export class SearchResultItemComponent implements OnInit {

  public searchResult: any;
  public objectId: string;
  modalRef: BsModalRef;

  constructor(
    private qb: QueryBuilderService,
    private route: ActivatedRoute,
    private router: Router,
    private modalService: BsModalService
    ) { }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params.id) {
        this.objectId = params.id;
        this.qb.getObjectMetadata(this.objectId)
          .subscribe(result => {
            this.searchResult = result;
          });
      }
    });
  }

  openModal(template: TemplateRef<any>) {
    this.modalRef = this.modalService.show(template);
  }

  useForPlot() {
    this.router.navigate([`/plot/options/${this.objectId}`]);
  }

}
