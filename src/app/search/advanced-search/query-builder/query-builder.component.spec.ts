import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { QueryBuilderComponent } from './query-builder.component';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { MockComponent } from 'ng-mocks';
import { PropertyParamsComponent } from './property-params/property-params.component';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { Subject } from 'rxjs';
import { QueryMatch } from 'src/app/shared/models/QueryBuilder';
import { NgSelectModule } from '@ng-select/ng-select';
import { FormsModule } from '@angular/forms';

describe('QueryBuilderComponent', () => {

  const MockQueryBuilder = {
    getDataTypes: () => new Subject(),
    getLoadedDataTypes: () => [{test: 'test'}]
  };

  let spectator: Spectator<QueryBuilderComponent>;
  const createComponent = createComponentFactory({
    component: QueryBuilderComponent,
    imports: [
      HttpClientModule,
      RouterModule.forRoot([]),
      NgSelectModule,
      FormsModule
    ],
    entryComponents: [
      MockComponent(PropertyParamsComponent)
    ],
    providers: [
      mockProvider(QueryBuilderService, MockQueryBuilder)
    ],
  });

  beforeEach(() => spectator = createComponent({
    props: {
      queryMatch: new QueryMatch()
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should load data types', () => {
    expect(spectator.component.dataTypes).toEqual([{test: 'test'}]);
  });

  it('should disable propertyParams until type is selected', () => {
    expect('button.btn.btn-link').toBeDisabled();

    spectator.component.selectedDataType = {
      dataType: 'test data type',
      dataModel: 'test data model',
      category: 'test category'
    };
    spectator.detectChanges();
    expect('button.btn.btn-link').not.toBeDisabled();
  });

  it('should render new property params', () => {
    spectator.component.selectedDataType = {
      dataType: 'test data type',
      dataModel: 'test data model',
      category: 'test category'
    };
    spectator.component.addPropertyParam();
    spectator.detectChanges();
    expect(spectator.query('app-property-params')).not.toBeNull();
  });
});
