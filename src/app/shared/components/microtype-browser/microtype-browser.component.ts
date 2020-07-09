import { Component, OnInit, ChangeDetectorRef, ViewChild, OnDestroy } from '@angular/core';
import { UploadService } from '../../services/upload.service';
import * as $ from 'jquery';
import 'datatables.net-bs4';
import 'datatables.net';
import { NgxSpinnerService } from 'ngx-spinner';
import { MicrotypeTreeService } from 'src/app/shared/services/microtype-tree.service';
import { MicroTypeTreeNode } from 'src/app/shared/models/microtype-tree';
import { ITreeOptions, TreeComponent, TreeModel } from 'angular-tree-component'
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { Subscription, Subject } from 'rxjs';

@Component({
  selector: 'app-microtype-browser',
  templateUrl: './microtype-browser.component.html',
  styleUrls: ['./microtype-browser.component.css']
})
export class MicrotypeBrowserComponent implements OnInit, OnDestroy {

  public microtypes: MicroTypeTreeNode[];
  dataTables: any;
  public treeOptions: ITreeOptions = { displayField: 'term_def' }
  textInputChanged: Subject<string> = new Subject();

  @ViewChild('tree', {static: false}) tree: TreeComponent;

  filters = {
    mt_dim_var: true,
    mt_dimension: true,
    mt_data_var: true,
    mt_property: true
  }

  constructor(
    private uploadService: UploadService,
    private chRef: ChangeDetectorRef,
    private spinner: NgxSpinnerService,
    private treeService: MicrotypeTreeService
  ) {
    // subscription for debouncing input search
    this.textInputChanged.pipe(
      debounceTime(300),
      distinctUntilChanged()
    )
    .subscribe(value => this.tree.treeModel.filterNodes(value))
  }

  ngOnInit() {
    this.treeService.getMicrotypes()
      .then((microtypes: MicroTypeTreeNode[]) => {
        this.microtypes = microtypes;
        this.chRef.detectChanges();
      });
  }

  ngOnDestroy() {
    this.textInputChanged.unsubscribe();
  }

  setKeywordSearchFilter(event) {
    // emit new keyword to be debounced and then filtered
    this.textInputChanged.next(event.target.value);
  }

  setCategoryFilter(event) {
    const checkedKeys = Object.keys(this.filters).filter(key => this.filters[key]);
    this.tree.treeModel.filterNodes((node) => {
      for (const key of checkedKeys) {
        if (node.data[key]) { return true; }
      }
      return false;
    });
  }

  descriptionVisible(node) {
    if (`${node.data.term_name}.` === node.data.term_desc) {
      return false;
    }
    return node.isExpanded || node.children.length;
  }

}
