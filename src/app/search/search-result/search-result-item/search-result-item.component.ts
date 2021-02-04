import { Component, OnInit } from '@angular/core';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { ActivatedRoute, Router } from '@angular/router';
import { DimensionVariablePreviewComponent as DimVarPreview } from '../dimension-variable-preview/dimension-variable-preview.component';
import { ObjectMetadata } from 'src/app/shared/models/object-metadata';

@Component({
  selector: 'app-search-result-item',
  templateUrl: './search-result-item.component.html',
  styleUrls: ['./search-result-item.component.css']
})
export class SearchResultItemComponent implements OnInit {

  public searchResult: ObjectMetadata;
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
          .subscribe((result: ObjectMetadata) => {
            this.searchResult = result;
          });
      }
    });
  }

  openModal(dimension: any, index: number) {
    this.qb.getDimensionVariableValues(this.objectId, index)
      .subscribe((res: any) => {
        const initialState = {
          data: res.results,
          title: dimension.data_type.oterm_name
        };
        this.modalRef = this.modalService.show(DimVarPreview, {initialState, class: 'modal-lg'});
      });
  }

  useForPlot() {
    this.qb.setPreviousUrl(`/search/result/brick/${this.objectId}`);
    this.router.navigate([`/plot/options/${this.objectId}`]);
  }

}
