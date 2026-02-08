/**
 * Distillation Workbench - Main Component
 *
 * A workbench for collecting, comparing, structuring, and reviewing
 * model responses to build high-quality training datasets.
 *
 * Refactored to use modular components and custom hook.
 */
import { FlaskConical, RefreshCw } from 'lucide-react'
import { useDistillation } from '../hooks/useDistillation'
import {
  Sidebar,
  ChatView,
  TasksView,
  BankView,
  CompareView,
  StructureView,
  DatasetsView,
  ReviewView,
  StatsView,
  TagModal,
  CreateDatasetModal,
  StructureModal,
  CreateTaskModal,
  CreateQueueModal
} from '../components/distillation'

export default function DistillationWorkbench() {
  const [state, actions] = useDistillation()

  return (
    <div className="min-h-screen p-6" style={{
      background: 'linear-gradient(135deg, #0a0a12 0%, #1a1a2e 50%, #16213e 100%)'
    }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <FlaskConical className="h-8 w-8" style={{ color: '#a8d8ff' }} />
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>
              Distillation Workbench
            </h1>
            <p className="text-sm" style={{ color: '#b3d9ff' }}>
              Collect, compare, and curate training data
            </p>
          </div>
        </div>
        <button
          onClick={actions.refreshAll}
          className="p-2 rounded-lg hover:bg-white/10 transition-all"
          style={{ color: '#a8d8ff' }}
          title="Refresh all data"
        >
          <RefreshCw className="h-5 w-5" />
        </button>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Sidebar */}
        <Sidebar
          viewMode={state.viewMode}
          setViewMode={actions.setViewMode}
          statistics={state.statistics}
          structuredItems={state.structuredItems}
          datasets={state.datasets}
        />

        {/* Main Content */}
        <div className="lg:col-span-4 space-y-4">
          {/* Chat View */}
          {state.viewMode === 'chat' && (
            <ChatView
              chatMessage={state.chatMessage}
              setChatMessage={actions.setChatMessage}
              selectedModels={state.selectedModels}
              setSelectedModels={actions.setSelectedModels}
              chatResponses={state.chatResponses}
              chatLoading={state.chatLoading}
              streamingStatus={state.streamingStatus}
              streamingContent={state.streamingContent}
              activeModel={state.activeModel}
              availableModels={state.availableModels}
              apiKeys={state.apiKeys}
              loadingModels={state.loadingModels}
              handleChat={actions.handleChat}
              handleBankResponse={actions.handleBankResponse}
              setTagResponseId={actions.setTagResponseId}
              setTagModalOpen={actions.setTagModalOpen}
            />
          )}

          {/* Tasks View */}
          {state.viewMode === 'tasks' && (
            <TasksView
              tasks={state.tasks}
              setCreateTaskOpen={actions.setCreateTaskOpen}
            />
          )}

          {/* Bank View */}
          {state.viewMode === 'bank' && (
            <BankView
              responses={state.responses}
              domains={state.domains}
              topics={state.topics}
              loading={state.loading}
              searchQuery={state.searchQuery}
              setSearchQuery={actions.setSearchQuery}
              filterProvider={state.filterProvider}
              setFilterProvider={actions.setFilterProvider}
              searchResponses={actions.searchResponses}
              handleDeleteResponse={actions.handleDeleteResponse}
              handleUpdateResponse={actions.handleUpdateResponse}
              handleBankResponse={actions.handleBankResponse}
              setTagResponseId={actions.setTagResponseId}
              setTagModalOpen={actions.setTagModalOpen}
            />
          )}

          {/* Compare View */}
          {state.viewMode === 'compare' && (
            <CompareView
              comparisons={state.comparisons}
              selectedComparison={state.selectedComparison}
              comparisonLoading={state.comparisonLoading}
              blindMode={state.blindMode}
              setBlindMode={actions.setBlindMode}
              selectedWinner={state.selectedWinner}
              setSelectedWinner={actions.setSelectedWinner}
              setSelectedComparison={actions.setSelectedComparison}
              loadComparisonDetails={actions.loadComparisonDetails}
              handleSubmitVote={actions.handleSubmitVote}
            />
          )}

          {/* Structure View */}
          {state.viewMode === 'structure' && (
            <StructureView
              schemas={state.schemas}
              bankedItems={state.bankedItems}
              structuredItems={state.structuredItems}
              datasets={state.datasets}
              selectedSchema={state.selectedSchema}
              setSelectedSchema={actions.setSelectedSchema}
              extracting={state.extracting}
              handleLLMExtract={actions.handleLLMExtract}
              setSelectedBanked={actions.setSelectedBanked}
              setStructureModalOpen={actions.setStructureModalOpen}
              handleAddToDataset={actions.handleAddToDataset}
            />
          )}

          {/* Datasets View */}
          {state.viewMode === 'datasets' && (
            <DatasetsView
              datasets={state.datasets}
              selectedDataset={state.selectedDataset}
              datasetStats={state.datasetStats}
              datasetItems={state.datasetItems}
              setCreateDatasetOpen={actions.setCreateDatasetOpen}
              setSelectedDataset={actions.setSelectedDataset}
              setDatasetStats={actions.setDatasetStats}
              setDatasetItems={actions.setDatasetItems}
              loadDatasetDetails={actions.loadDatasetDetails}
              loadDatasets={actions.loadDatasets}
              handleExportDataset={actions.handleExportDataset}
            />
          )}

          {/* Review View */}
          {state.viewMode === 'review' && (
            <ReviewView
              reviewQueues={state.reviewQueues}
              selectedQueue={state.selectedQueue}
              reviewItems={state.reviewItems}
              currentReviewItem={state.currentReviewItem}
              reviewLoading={state.reviewLoading}
              reviewNotes={state.reviewNotes}
              setReviewNotes={actions.setReviewNotes}
              reviewScore={state.reviewScore}
              setReviewScore={actions.setReviewScore}
              setCreateQueueOpen={actions.setCreateQueueOpen}
              setSelectedQueue={actions.setSelectedQueue}
              setReviewItems={actions.setReviewItems}
              setCurrentReviewItem={actions.setCurrentReviewItem}
              loadReviewItems={actions.loadReviewItems}
              getNextReviewItem={actions.getNextReviewItem}
              handleAutoPopulateQueue={actions.handleAutoPopulateQueue}
              handleExportQueue={actions.handleExportQueue}
              handleSubmitReview={actions.handleSubmitReview}
            />
          )}

          {/* Stats View */}
          {state.viewMode === 'stats' && (
            <StatsView
              statistics={state.statistics}
              modelPreferences={state.modelPreferences}
              structuredItems={state.structuredItems}
              datasets={state.datasets}
            />
          )}
        </div>
      </div>

      {/* Modals */}
      <TagModal
        open={state.tagModalOpen}
        onClose={() => actions.setTagModalOpen(false)}
        tags={state.tags}
        newTagName={state.newTagName}
        setNewTagName={actions.setNewTagName}
        handleAddTags={actions.handleAddTags}
      />

      <CreateDatasetModal
        open={state.createDatasetOpen}
        onClose={() => actions.setCreateDatasetOpen(false)}
        newDataset={state.newDataset}
        setNewDataset={actions.setNewDataset}
        handleCreateDataset={actions.handleCreateDataset}
      />

      <StructureModal
        open={state.structureModalOpen}
        onClose={() => actions.setStructureModalOpen(false)}
        selectedBanked={state.selectedBanked}
        schemas={state.schemas}
        selectedSchema={state.selectedSchema}
        setSelectedSchema={actions.setSelectedSchema}
        structuredData={state.structuredData}
        setStructuredData={actions.setStructuredData}
        handleSaveStructured={actions.handleSaveStructured}
      />

      <CreateTaskModal
        open={state.createTaskOpen}
        onClose={() => actions.setCreateTaskOpen(false)}
        newTask={state.newTask}
        setNewTask={actions.setNewTask}
        handleCreateTask={actions.handleCreateTask}
        taskLoading={state.taskLoading}
        domains={state.domains}
        topics={state.topics}
        availableModels={state.availableModels}
        apiKeys={state.apiKeys}
      />

      <CreateQueueModal
        open={state.createQueueOpen}
        onClose={() => actions.setCreateQueueOpen(false)}
        newQueue={state.newQueue}
        setNewQueue={actions.setNewQueue}
        handleCreateQueue={actions.handleCreateQueue}
      />
    </div>
  )
}
