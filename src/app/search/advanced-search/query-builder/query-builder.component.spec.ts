import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { QueryBuilderComponent } from './query-builder.component';
import { Select2Module } from 'ng2-select2';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { MockComponent } from 'ng-mocks';
import { PropertyParamsComponent } from './property-params/property-params.component';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { Subject } from 'rxjs';

fdescribe('QueryBuilderComponent', () => {

  const MockQueryBuilder = {
    getDataTypes: () => new Subject(),
    getLoadedDataTypes: () => [{test: 'test'}]
  };

  let spectator: Spectator<QueryBuilderComponent>;
  const createComponent = createComponentFactory({
    component: QueryBuilderComponent,
    imports: [
      Select2Module,
      HttpClientModule,
      RouterModule.forRoot([])
    ],
    entryComponents: [
      MockComponent(PropertyParamsComponent)
    ],
    providers: [
      mockProvider(QueryBuilderService, MockQueryBuilder)
    ],
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should load data types', () => {
    const spy = spyOn(spectator.component, 'populateDataTypes').and.callThrough();
    expect(spy);
    expect(spectator.component.dataTypes).toEqual([{test: 'test'}]);
  });
});
